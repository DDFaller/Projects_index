"""Prometheus metrics for the portfolio and URL shortener API."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram


API_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests handled by the API.",
    ("method", "route", "status"),
)
API_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ("method", "route"),
)
SHORTENER_LINKS_CREATED = Counter(
    "shortener_links_created_total",
    "Short links successfully created.",
)
SHORTENER_REDIRECTS = Counter(
    "shortener_redirects_total",
    "Short-link resolution attempts by outcome.",
    ("outcome",),
)
SHORTENER_RATE_LIMITED = Counter(
    "shortener_rate_limited_total",
    "Shortener requests rejected by the rate limiter.",
)
SHORTENER_LINKS_IN_MEMORY = Gauge(
    "shortener_links_in_memory",
    "Links currently held by the process-local demo repository.",
)
