"""Tests for JiraClient."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from pyacli.lib.client import JiraClient
from pyacli.lib.dto import JiraIssue
from pyacli.lib.exceptions import AcliValidationError
from pyacli.lib.runner import AcliResult, AcliRunner
from pyacli.lib.schemas import CreateIssueRequest, SearchIssuesRequest
from tests.conftest import SAMPLE_ISSUE_JSON, SAMPLE_SEARCH_JSON


@pytest.fixture
def client(mock_runner: AcliRunner) -> JiraClient:
    """JiraClient with mocked runner."""
    return JiraClient(project="WNVO", runner=mock_runner)


class TestCreateIssue:
    """Tests for JiraClient.create_issue()."""

    async def test_with_kwargs(self, client: JiraClient, mock_runner: MagicMock) -> None:
        mock_runner.run_json.return_value = SAMPLE_ISSUE_JSON

        issue = await client.create_issue(
            summary="New task",
            description="Details",
            labels=["bug"],
        )

        assert isinstance(issue, JiraIssue)
        assert issue.key == "WNVO-110"
        mock_runner.run_json.assert_awaited_once()

        call_args = mock_runner.run_json.call_args[0]
        assert "--summary" in call_args
        assert "New task" in call_args
        assert "--project" in call_args
        assert "WNVO" in call_args

    async def test_with_request(self, client: JiraClient, mock_runner: MagicMock) -> None:
        mock_runner.run_json.return_value = SAMPLE_ISSUE_JSON

        req = CreateIssueRequest(summary="Via request", type="Bug")
        issue = await client.create_issue(request=req)

        assert issue.key == "WNVO-110"
        call_args = mock_runner.run_json.call_args[0]
        assert "Bug" in call_args

    async def test_missing_summary_and_request(self, client: JiraClient) -> None:
        with pytest.raises(AcliValidationError, match="summary"):
            await client.create_issue()


class TestGetIssue:
    """Tests for JiraClient.get_issue()."""

    async def test_get_issue(self, client: JiraClient, mock_runner: MagicMock) -> None:
        mock_runner.run_json.return_value = SAMPLE_ISSUE_JSON

        issue = await client.get_issue("WNVO-110")

        assert issue.key == "WNVO-110"
        assert issue.summary == "적성검사 결과 렌더링"

        call_args = mock_runner.run_json.call_args[0]
        assert "WNVO-110" in call_args
        assert "--json" in call_args


class TestSearchIssues:
    """Tests for JiraClient.search_issues()."""

    async def test_with_jql(self, client: JiraClient, mock_runner: MagicMock) -> None:
        mock_runner.run_json.return_value = SAMPLE_SEARCH_JSON

        issues = await client.search_issues(jql="project = WNVO")

        assert len(issues) == 1
        assert issues[0].key == "WNVO-110"

        call_args = mock_runner.run_json.call_args[0]
        assert "--jql" in call_args
        assert "project = WNVO" in call_args

    async def test_with_request(self, client: JiraClient, mock_runner: MagicMock) -> None:
        mock_runner.run_json.return_value = SAMPLE_SEARCH_JSON

        req = SearchIssuesRequest(jql="project = WNVO", limit=10)
        issues = await client.search_issues(request=req)

        assert len(issues) == 1
        call_args = mock_runner.run_json.call_args[0]
        assert "10" in call_args

    async def test_empty_result(self, client: JiraClient, mock_runner: MagicMock) -> None:
        mock_runner.run_json.return_value = []

        issues = await client.search_issues(jql="project = EMPTY")
        assert issues == []

    async def test_missing_jql_and_request(self, client: JiraClient) -> None:
        with pytest.raises(AcliValidationError, match="jql"):
            await client.search_issues()


class TestTransitionIssue:
    """Tests for JiraClient.transition_issue()."""

    async def test_transition(self, client: JiraClient, mock_runner: MagicMock) -> None:
        mock_runner.run.return_value = AcliResult(0, "", "")

        result = await client.transition_issue("WNVO-110", status="Done")

        assert result is None
        call_args = mock_runner.run.call_args[0]
        assert "--key" in call_args
        assert "WNVO-110" in call_args
        assert "--status" in call_args
        assert "Done" in call_args
        assert "--yes" in call_args
