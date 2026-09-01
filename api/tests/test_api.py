import pytest
from fastapi import HTTPException

from api.app import get_project, health, list_projects


def test_health_returns_service_metadata() -> None:
    response = health()

    assert response["service"] == "faller-index-api"


def test_projects_are_paginated() -> None:
    response = list_projects(page=1, page_size=2)

    assert response.total == 4
    assert len(response.results) == 2
    assert response.pages == 2


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
