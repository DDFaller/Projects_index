"""HTTP API for the Faller / Index project catalogue.

The first slice uses a versioned JSON catalogue so the API and search contract
can be exercised before introducing PostgreSQL persistence.
"""

from __future__ import annotations

import json
import math
import re
import time
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from api.observability import API_REQUESTS, API_REQUEST_DURATION, SHORTENER_REDIRECTS
from api.shortener import (
    ShortLinkCreate,
    ShortLinkResponse,
    ShortLinkStats,
    _active_record,
    analytics_event,
    create_link,
    enforce_rate_limit,
    link_response,
    link_stats,
    redirect_cache,
    repository,
)


CATALOG_PATH = Path(__file__).parent / "data" / "projects.json"
SITE_ROOT = Path(__file__).resolve().parent.parent


class Project(BaseModel):
    """Public representation of a portfolio project."""

    model_config = ConfigDict(extra="forbid")

    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str
    eyebrow: str
    description: str
    technologies: list[str]
    categories: list[str]
    image_url: str | None = None
    embed_url: str | None = None
    demo_url: str | None = None
    repo_url: str | None = None
    featured: bool = False


class ProjectSearchResponse(BaseModel):
    """Paginated project search response."""

    results: list[Project]
    query: str | None
    category: str | None
    technology: str | None
    page: int
    page_size: int
    total: int
    pages: int


def load_catalog() -> list[Project]:
    """Load and validate the catalogue at startup."""

    with CATALOG_PATH.open(encoding="utf-8") as catalog_file:
        raw_projects = json.load(catalog_file)
    return [Project.model_validate(project) for project in raw_projects]


CATALOG = load_catalog()


app = FastAPI(
    title="Faller / Index API",
    summary="Searchable portfolio catalogue and URL shortener with redirect analytics.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    """Record bounded-label request metrics for Prometheus and Grafana."""

    if request.url.path == "/metrics":
        return await call_next(request)

    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        route = getattr(request.scope.get("route"), "path", "unmatched")
        API_REQUESTS.labels(request.method, route, "500").inc()
        API_REQUEST_DURATION.labels(request.method, route).observe(
            time.perf_counter() - started_at
        )
        raise

    route = getattr(request.scope.get("route"), "path", "unmatched")
    API_REQUESTS.labels(request.method, route, str(response.status_code)).inc()
    API_REQUEST_DURATION.labels(request.method, route).observe(
        time.perf_counter() - started_at
    )
    return response


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _relevance(project: Project, query: str) -> int:
    """Score a project so title and technology matches rank first."""

    normalized_query = query.strip().lower()
    if not normalized_query:
        return 0

    score = 0
    searchable_title = project.title.lower()
    searchable_eyebrow = project.eyebrow.lower()
    searchable_description = project.description.lower()
    searchable_technologies = " ".join(project.technologies).lower()
    searchable_categories = " ".join(project.categories).lower()

    if normalized_query in searchable_title:
        score += 10
    if normalized_query in searchable_eyebrow:
        score += 5
    if normalized_query in searchable_technologies:
        score += 4
    if normalized_query in searchable_categories:
        score += 3
    if normalized_query in searchable_description:
        score += 2

    query_tokens = _tokens(normalized_query)
    searchable_tokens = (
        _tokens(project.title)
        | _tokens(project.eyebrow)
        | _tokens(project.description)
        | _tokens(searchable_technologies)
        | _tokens(searchable_categories)
    )
    score += len(query_tokens & searchable_tokens)
    return score


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Return a lightweight liveness response."""

    return {"status": "ok", "service": "faller-index-api", "version": app.version}


@app.get("/ready", tags=["system"])
def readiness() -> dict[str, str]:
    """Return the readiness response used by deployment health checks."""

    return {"status": "ready", "storage": "in-memory-demo", "cache": "in-memory-demo"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    """Expose Prometheus text-format metrics for local observability."""

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/projects", response_model=ProjectSearchResponse, tags=["projects"])
def list_projects(
    query: Annotated[str | None, Query(alias="q", max_length=80)] = None,
    category: Annotated[str | None, Query(max_length=40)] = None,
    technology: Annotated[str | None, Query(max_length=40)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 12,
) -> ProjectSearchResponse:
    """List, filter, and relevance-rank catalogue projects."""

    normalized_category = category.strip().lower() if category else None
    normalized_technology = technology.strip().lower() if technology else None
    filtered = [
        project
        for project in CATALOG
        if (
            not normalized_category
            or normalized_category in {item.lower() for item in project.categories}
        )
        and (
            not normalized_technology
            or normalized_technology in {item.lower() for item in project.technologies}
        )
    ]

    normalized_query = query.strip() if query else None
    if normalized_query:
        filtered = [project for project in filtered if _relevance(project, normalized_query) > 0]
        filtered.sort(
            key=lambda project: (-_relevance(project, normalized_query), not project.featured, project.title)
        )
    else:
        filtered.sort(key=lambda project: (not project.featured, project.title))

    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    pages = math.ceil(total / page_size) if total else 0

    return ProjectSearchResponse(
        results=filtered[start:end],
        query=normalized_query,
        category=category,
        technology=technology,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


@app.get("/api/v1/projects/{slug}", response_model=Project, tags=["projects"])
def get_project(slug: str) -> Project:
    """Return one project by its stable slug."""

    for project in CATALOG:
        if project.slug == slug:
            return project
    raise HTTPException(status_code=404, detail="Project not found")


@app.post(
    "/api/v1/short-links",
    response_model=ShortLinkResponse,
    status_code=201,
    tags=["short-links"],
)
def create_short_link(payload: ShortLinkCreate, request: Request) -> ShortLinkResponse:
    """Create a short link with an optional custom alias and expiration."""

    enforce_rate_limit(request)
    record = create_link(payload)
    return link_response(record, str(request.base_url))


@app.get("/r/{code}", response_class=RedirectResponse, include_in_schema=False)
def redirect_short_link(code: str, request: Request) -> RedirectResponse:
    """Resolve a link, record its click, and redirect to the target URL."""

    enforce_rate_limit(request)
    try:
        record = _active_record(code)
    except HTTPException as error:
        outcome = {
            404: "not_found",
            410: "inactive",
        }.get(error.status_code, "error")
        SHORTENER_REDIRECTS.labels(outcome).inc()
        raise
    repository.add_event(record, analytics_event(request))
    SHORTENER_REDIRECTS.labels("success").inc()
    return RedirectResponse(record.target_url, status_code=307)


@app.get("/api/v1/short-links/{code}/stats", response_model=ShortLinkStats, tags=["short-links"])
def short_link_stats(code: str, request: Request) -> ShortLinkStats:
    """Return aggregate click analytics for a short link."""

    enforce_rate_limit(request)
    record = repository.get(code)
    if record is None:
        raise HTTPException(status_code=404, detail="Short link not found")
    return link_stats(record, str(request.base_url))


@app.post("/api/v1/short-links/{code}/disable", response_model=ShortLinkResponse, tags=["short-links"])
def disable_short_link(code: str, request: Request) -> ShortLinkResponse:
    """Disable a link and evict it from the redirect cache."""

    enforce_rate_limit(request)
    record = repository.disable(code)
    redirect_cache.invalidate(code)
    return link_response(record, str(request.base_url))


@app.get("/", include_in_schema=False)
def portfolio_home() -> FileResponse:
    """Serve the portfolio homepage from the same Vercel deployment."""

    return FileResponse(SITE_ROOT / "index.html", media_type="text/html")


@app.get("/styles.css", include_in_schema=False)
def portfolio_styles() -> FileResponse:
    """Serve the portfolio stylesheet when Vercel routes the request to FastAPI."""

    return FileResponse(SITE_ROOT / "styles.css", media_type="text/css")


@app.get("/app.js", include_in_schema=False)
def portfolio_script() -> FileResponse:
    """Serve the portfolio browser client."""

    return FileResponse(SITE_ROOT / "app.js", media_type="application/javascript")


app.mount("/images", StaticFiles(directory=SITE_ROOT / "images"), name="portfolio-images")
