"""URL shortener domain logic.

The repository and cache are intentionally process-local for the first
deployable slice.  They are isolated behind small classes so they can be
replaced by PostgreSQL and Redis without changing the HTTP contract.
"""

from __future__ import annotations

import os
import re
import secrets
import string
import threading
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from api.observability import (
    SHORTENER_LINKS_CREATED,
    SHORTENER_LINKS_IN_MEMORY,
    SHORTENER_RATE_LIMITED,
)

if TYPE_CHECKING:
    from starlette.requests import Request


CODE_ALPHABET = string.ascii_letters + string.digits
CODE_PATTERN = r"^[A-Za-z0-9_-]+$"
DEFAULT_RATE_LIMIT = 60
RATE_WINDOW_SECONDS = 60


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalise_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class ShortLinkCreate(BaseModel):
    """Payload for creating a short link."""

    model_config = ConfigDict(extra="forbid")

    target_url: str = Field(min_length=1, max_length=2_048)
    alias: str | None = Field(default=None, min_length=4, max_length=32)
    expires_at: datetime | None = None

    @field_validator("target_url")
    @classmethod
    def validate_target_url(cls, value: str) -> str:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("target_url must be an absolute HTTP(S) URL")
        return value

    @field_validator("alias")
    @classmethod
    def validate_alias(cls, value: str | None) -> str | None:
        if value is not None and not re.match(CODE_PATTERN, value):
            raise ValueError("alias may contain only letters, numbers, '-' or '_'")
        return value

    @field_validator("expires_at")
    @classmethod
    def validate_expiration(cls, value: datetime | None) -> datetime | None:
        value = _normalise_datetime(value)
        if value is not None and value <= utc_now():
            raise ValueError("expires_at must be in the future")
        return value


class ShortLinkResponse(BaseModel):
    """Public short-link representation."""

    model_config = ConfigDict(extra="forbid")

    code: str
    short_url: str
    target_url: str
    created_at: datetime
    expires_at: datetime | None
    disabled: bool


class ShortLinkStats(BaseModel):
    """Small analytics summary that does not expose visitor IP addresses."""

    model_config = ConfigDict(extra="forbid")

    code: str
    short_url: str
    target_url: str
    created_at: datetime
    expires_at: datetime | None
    disabled: bool
    clicks: int
    last_clicked_at: datetime | None
    referrers: dict[str, int]
    user_agents: dict[str, int]


@dataclass(slots=True)
class ClickEvent:
    clicked_at: datetime
    referrer: str
    user_agent: str


@dataclass(slots=True)
class LinkRecord:
    code: str
    target_url: str
    created_at: datetime
    expires_at: datetime | None
    disabled: bool = False
    events: list[ClickEvent] = field(default_factory=list)

    @property
    def active(self) -> bool:
        return not self.disabled and (
            self.expires_at is None or self.expires_at > utc_now()
        )


class InMemoryLinkRepository:
    """Thread-safe repository used by local development and the demo deploy."""

    def __init__(self) -> None:
        self._links: dict[str, LinkRecord] = {}
        self._lock = threading.RLock()

    def create(self, target_url: str, alias: str | None, expires_at: datetime | None) -> LinkRecord:
        with self._lock:
            code = alias or self._new_code()
            if code in self._links:
                raise HTTPException(status_code=409, detail="Alias is already in use")
            record = LinkRecord(
                code=code,
                target_url=target_url,
                created_at=utc_now(),
                expires_at=expires_at,
            )
            self._links[code] = record
            SHORTENER_LINKS_CREATED.inc()
            SHORTENER_LINKS_IN_MEMORY.set(len(self._links))
            return record

    def get(self, code: str) -> LinkRecord | None:
        with self._lock:
            return self._links.get(code)

    def disable(self, code: str) -> LinkRecord:
        with self._lock:
            record = self._links.get(code)
            if record is None:
                raise HTTPException(status_code=404, detail="Short link not found")
            record.disabled = True
            return record

    def add_event(self, record: LinkRecord, event: ClickEvent) -> None:
        with self._lock:
            record.events.append(event)

    def clear(self) -> None:
        with self._lock:
            self._links.clear()
            SHORTENER_LINKS_IN_MEMORY.set(0)

    def _new_code(self) -> str:
        for _ in range(10):
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(7))
            if code not in self._links:
                return code
        raise HTTPException(status_code=503, detail="Could not allocate a short code")


class RedirectCache:
    """Tiny hot-link cache; replace with Redis for multi-instance deployments."""

    def __init__(self) -> None:
        self._records: dict[str, LinkRecord] = {}
        self._lock = threading.RLock()

    def get(self, code: str) -> LinkRecord | None:
        with self._lock:
            return self._records.get(code)

    def put(self, record: LinkRecord) -> None:
        with self._lock:
            self._records[record.code] = record

    def invalidate(self, code: str) -> None:
        with self._lock:
            self._records.pop(code, None)

    def clear(self) -> None:
        with self._lock:
            self._records.clear()


class FixedWindowRateLimiter:
    """A bounded per-key fixed-window limiter for the API demo."""

    def __init__(self, limit: int = DEFAULT_RATE_LIMIT, window_seconds: int = RATE_WINDOW_SECONDS) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._windows: dict[str, tuple[datetime, int]] = {}
        self._lock = threading.RLock()

    def allow(self, key: str) -> bool:
        now = utc_now()
        with self._lock:
            window = self._windows.get(key)
            if window is None or now - window[0] >= timedelta(seconds=self.window_seconds):
                self._windows[key] = (now, 1)
                return True
            started_at, count = window
            if count >= self.limit:
                return False
            self._windows[key] = (started_at, count + 1)
            return True

    def clear(self) -> None:
        with self._lock:
            self._windows.clear()


repository = InMemoryLinkRepository()
redirect_cache = RedirectCache()
rate_limiter = FixedWindowRateLimiter(
    limit=max(1, int(os.getenv("SHORTENER_RATE_LIMIT", str(DEFAULT_RATE_LIMIT))))
)


def request_key(request: Request | None) -> str:
    """Get the client key used for rate limiting behind a trusted proxy."""

    if request is None:
        return "local-test"
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", maxsplit=1)[0].strip()
    return request.client.host if request.client else "unknown-client"


def enforce_rate_limit(request: Request | None) -> None:
    if not rate_limiter.allow(request_key(request)):
        SHORTENER_RATE_LIMITED.inc()
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


def _active_record(code: str) -> LinkRecord:
    record = redirect_cache.get(code)
    if record is None:
        record = repository.get(code)
        if record is not None and record.active:
            redirect_cache.put(record)
    if record is None:
        raise HTTPException(status_code=404, detail="Short link not found")
    if record.disabled:
        redirect_cache.invalidate(code)
        raise HTTPException(status_code=410, detail="Short link is disabled")
    if record.expires_at is not None and record.expires_at <= utc_now():
        redirect_cache.invalidate(code)
        raise HTTPException(status_code=410, detail="Short link has expired")
    return record


def create_link(payload: ShortLinkCreate) -> LinkRecord:
    return repository.create(
        target_url=payload.target_url,
        alias=payload.alias,
        expires_at=payload.expires_at,
    )


def link_response(record: LinkRecord, base_url: str) -> ShortLinkResponse:
    return ShortLinkResponse(
        code=record.code,
        short_url=f"{base_url.rstrip('/')}/r/{record.code}",
        target_url=record.target_url,
        created_at=record.created_at,
        expires_at=record.expires_at,
        disabled=record.disabled,
    )


def link_stats(record: LinkRecord, base_url: str) -> ShortLinkStats:
    referrers = Counter(event.referrer for event in record.events)
    user_agents = Counter(event.user_agent for event in record.events)
    return ShortLinkStats(
        code=record.code,
        short_url=f"{base_url.rstrip('/')}/r/{record.code}",
        target_url=record.target_url,
        created_at=record.created_at,
        expires_at=record.expires_at,
        disabled=record.disabled,
        clicks=len(record.events),
        last_clicked_at=record.events[-1].clicked_at if record.events else None,
        referrers=dict(referrers.most_common(10)),
        user_agents=dict(user_agents.most_common(10)),
    )


def analytics_event(request: Request | None) -> ClickEvent:
    headers = request.headers if request is not None else {}
    return ClickEvent(
        clicked_at=utc_now(),
        referrer=headers.get("referer", "direct"),
        user_agent=headers.get("user-agent", "unknown"),
    )
