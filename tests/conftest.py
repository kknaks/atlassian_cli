"""Shared test fixtures for pyacli."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyacli.lib.runner import AcliResult, AcliRunner


SAMPLE_ISSUE_JSON = {
    "id": "10163",
    "key": "WNVO-110",
    "self": "https://jira-prod-ap-31-2.prod.atl-paas.net/rest/api/3/issue/10163",
    "fields": {
        "summary": "적성검사 결과 렌더링",
        "description": None,
        "status": {
            "id": "10000",
            "name": "해야 할 일",
            "statusCategory": {
                "id": 2,
                "key": "new",
                "name": "해야 할 일",
                "colorName": "blue-gray",
            },
        },
        "issuetype": {"id": "10003", "name": "하위 작업", "subtask": True},
        "priority": {"id": "3", "name": "Medium"},
        "assignee": None,
        "creator": {
            "accountId": "712020:e3ee6ea8-cbfc-410b-8a90-970a8426826c",
            "displayName": "강진수",
            "active": True,
        },
        "reporter": {
            "accountId": "712020:e3ee6ea8-cbfc-410b-8a90-970a8426826c",
            "displayName": "강진수",
        },
        "project": {"id": "10000", "key": "WNVO", "name": "멋사로켓단"},
        "labels": [],
        "created": "2025-07-01T16:19:46.080+0900",
        "updated": "2025-07-01T16:19:46.213+0900",
        "parent": None,
        "duedate": None,
        "resolution": None,
    },
}

SAMPLE_SEARCH_JSON = [SAMPLE_ISSUE_JSON]


@pytest.fixture
def mock_runner() -> AcliRunner:
    """AcliRunner with mocked subprocess calls."""
    runner = MagicMock(spec=AcliRunner)
    runner.run = AsyncMock()
    runner.run_json = AsyncMock()
    return runner


@pytest.fixture
def sample_issue_json() -> dict:
    """Single issue JSON from acli."""
    return SAMPLE_ISSUE_JSON.copy()


@pytest.fixture
def sample_search_json() -> list:
    """Search result JSON from acli."""
    return [SAMPLE_ISSUE_JSON.copy()]
