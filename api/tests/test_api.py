import pytest
from fastapi import HTTPException
from starlette.requests import Request

from api.app import (
    SITE_ROOT,
    create_short_link,
    disable_short_link,
    get_project,
    health,
    list_projects,
    metrics,
    portfolio_home,
    redirect_short_link,
    short_link_stats,
)
from api.shortener import ShortLinkCreate, rate_limiter, redirect_cache, repository, utc_now


def make_request(headers: dict[str, str] | None = None) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [
            (key.lower().encode("latin-1"), value.encode("latin-1"))
            for key, value in (headers or {}).items()
        ],
        "client": ("127.0.0.1", 8000),
        "scheme": "http",
        "server": ("testserver", 80),
        "root_path": "",
    }
    return Request(scope)


@pytest.fixture(autouse=True)
def reset_shortener_state() -> None:
    repository.clear()
    redirect_cache.clear()
    rate_limiter.clear()
    rate_limiter.limit = 60


def test_health_returns_service_metadata() -> None:
    response = health()

    assert response["service"] == "faller-index-api"


def test_prometheus_metrics_endpoint_exposes_shortener_series() -> None:
    body = metrics().body.decode("utf-8")

    assert "shortener_links_created_total" in body
    assert "shortener_redirects_total" in body
    assert "http_request_duration_seconds" in body


def test_projects_are_paginated() -> None:
    response = list_projects(page=1, page_size=2)

    assert response.total == 8
    assert len(response.results) == 2
    assert response.pages == 4


def test_search_ranks_title_and_technology_matches() -> None:
    response = list_projects(query="webgl")

    assert response.results[0].slug == "cloth-simulation"


def test_category_filter_is_case_insensitive() -> None:
    response = list_projects(category="COMPUTER-VISION")

    assert {item.slug for item in response.results} == {
        "rgb-d-object-detection",
        "sports-action-tracking-thesis",
    }


def test_unknown_project_returns_not_found() -> None:
    with pytest.raises(HTTPException) as error:
        get_project("not-a-real-project")

    assert error.value.status_code == 404


def test_portfolio_home_points_to_existing_index() -> None:
    response = portfolio_home()

    assert response.path == SITE_ROOT / "index.html"
    assert SITE_ROOT.joinpath("styles.css").exists()
    assert SITE_ROOT.joinpath("app.js").exists()


def test_create_short_link_supports_custom_alias() -> None:
    response = create_short_link(
        ShortLinkCreate(
            target_url="https://example.com/docs",
            alias="docs-1",
        ),
        make_request(),
    )

    assert response.code == "docs-1"
    assert response.short_url == "http://testserver/r/docs-1"

    with pytest.raises(HTTPException) as error:
        create_short_link(
            ShortLinkCreate(target_url="https://example.com/other", alias="docs-1"),
            make_request(),
        )
    assert error.value.status_code == 409


def test_redirect_records_analytics_without_changing_target() -> None:
    request = make_request({"referer": "https://search.example", "user-agent": "pytest"})
    created = create_short_link(ShortLinkCreate(target_url="https://example.com"), request)

    redirect = redirect_short_link(created.code, request)
    stats = short_link_stats(created.code, request)

    assert redirect.status_code == 307
    assert redirect.headers["location"] == "https://example.com"
    assert stats.clicks == 1
    assert stats.referrers == {"https://search.example": 1}
    assert stats.user_agents == {"pytest": 1}


def test_expired_and_disabled_links_return_gone() -> None:
    with pytest.raises(ValueError):
        ShortLinkCreate(
            target_url="https://example.com/expired",
            expires_at="2000-01-01T00:00:00Z",
        )

    expired = repository.create(
        target_url="https://example.com/expired",
        alias="gone-1",
        expires_at=utc_now(),
    )
    with pytest.raises(HTTPException) as error:
        redirect_short_link(expired.code, make_request())
    assert error.value.status_code == 410

    created = create_short_link(ShortLinkCreate(target_url="https://example.com"), make_request())
    disable_short_link(created.code, make_request())

    with pytest.raises(HTTPException) as error:
        redirect_short_link(created.code, make_request())
    assert error.value.status_code == 410


def test_rate_limit_blocks_excessive_requests() -> None:
    rate_limiter.limit = 1
    request = make_request()
    create_short_link(ShortLinkCreate(target_url="https://example.com"), request)

    with pytest.raises(HTTPException) as error:
        create_short_link(ShortLinkCreate(target_url="https://example.com/2"), request)
    assert error.value.status_code == 429
