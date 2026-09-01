"""HTTP API for the Faller / Index project catalogue.

The first slice uses a versioned JSON catalogue so the API and search contract
can be exercised before introducing PostgreSQL persistence.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field


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
    summary="Searchable project catalogue for Daniel Faller's engineering portfolio.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


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
