"""Tests for JiraClient."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

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


SAMPLE_PROJECT_LIST_JSON = [
    {
        "id": "10000",
        "key": "WNVO",
        "name": "멋사로켓단",
        "projectTypeKey": "software",
        "style": "next-gen",
    },
    {
        "id": "10001",
        "key": "LEARNJIRA",
        "name": "(Learn) Jira Premium benefits",
        "projectTypeKey": "software",
        "style": "next-gen",
    },
]


class TestInit:
    """Tests for JiraClient initialization."""

    def test_project_from_arg(self, mock_runner: MagicMock) -> None:
        client = JiraClient(project="WNVO", runner=mock_runner)
        assert client.project == "WNVO"

    def test_project_from_env(self, mock_runner: MagicMock) -> None:
        with patch.dict("os.environ", {"PYACLI_DEFAULT_PROJECT": "FROM_ENV"}):
            client = JiraClient(runner=mock_runner)
            assert client.project == "FROM_ENV"

    def test_project_arg_overrides_env(self, mock_runner: MagicMock) -> None:
        with patch.dict("os.environ", {"PYACLI_DEFAULT_PROJECT": "FROM_ENV"}):
            client = JiraClient(project="FROM_ARG", runner=mock_runner)
            assert client.project == "FROM_ARG"

    def test_no_project(self, mock_runner: MagicMock) -> None:
        with patch.dict("os.environ", {}, clear=True):
            client = JiraClient(runner=mock_runner)
            assert client.project == ""

    async def test_create_issue_no_project_raises(self, mock_runner: MagicMock) -> None:
        with patch.dict("os.environ", {}, clear=True):
            client = JiraClient(runner=mock_runner)
            with pytest.raises(AcliValidationError, match="Project is required"):
                await client.create_issue(summary="test")

    async def test_list_issue_types_no_project_raises(self, mock_runner: MagicMock) -> None:
        with patch.dict("os.environ", {}, clear=True):
            client = JiraClient(runner=mock_runner)
            with pytest.raises(AcliValidationError, match="Project is required"):
                await client.list_issue_types()


class TestEpicMap:
    """Tests for epic map loading and resolution."""

    def test_epic_map_from_arg(self, mock_runner: MagicMock) -> None:
        epic_map = {"frontend": "WNVO-9", "backend": "WNVO-23"}
        client = JiraClient(project="WNVO", epic_map=epic_map, runner=mock_runner)
        assert client.epics == epic_map

    def test_epic_map_from_env(self, mock_runner: MagicMock) -> None:
        env = {"PYACLI_EPIC_MAP": "frontend:WNVO-9,backend:WNVO-23,ai:WNVO-24"}
        with patch.dict("os.environ", env):
            client = JiraClient(project="WNVO", runner=mock_runner)
            assert client.epics == {
                "frontend": "WNVO-9",
                "backend": "WNVO-23",
                "ai": "WNVO-24",
            }

    def test_epic_map_empty_env(self, mock_runner: MagicMock) -> None:
        with patch.dict("os.environ", {}, clear=True):
            client = JiraClient(project="WNVO", runner=mock_runner)
            assert client.epics == {}

    async def test_create_issue_with_epic(self, mock_runner: MagicMock) -> None:
        mock_runner.run_json = AsyncMock(return_value=SAMPLE_ISSUE_JSON)
        epic_map = {"frontend": "WNVO-9"}
        client = JiraClient(project="WNVO", epic_map=epic_map, runner=mock_runner)

        await client.create_issue(summary="Fix bug", epic="frontend")

        call_args = mock_runner.run_json.call_args[0]
        assert "--parent" in call_args
        assert "WNVO-9" in call_args

    async def test_create_issue_parent_overrides_epic(self, mock_runner: MagicMock) -> None:
        mock_runner.run_json = AsyncMock(return_value=SAMPLE_ISSUE_JSON)
        epic_map = {"frontend": "WNVO-9"}
        client = JiraClient(project="WNVO", epic_map=epic_map, runner=mock_runner)

        await client.create_issue(summary="Fix", parent="WNVO-99", epic="frontend")

        call_args = mock_runner.run_json.call_args[0]
        assert "WNVO-99" in call_args  # parent wins

    async def test_create_issue_unknown_epic_raises(self, mock_runner: MagicMock) -> None:
        epic_map = {"frontend": "WNVO-9"}
        client = JiraClient(project="WNVO", epic_map=epic_map, runner=mock_runner)

        with pytest.raises(AcliValidationError, match="not found in epic map"):
            await client.create_issue(summary="Fix", epic="unknown")


class TestListProjects:
    """Tests for JiraClient.list_projects()."""

    async def test_list_projects(self, client: JiraClient, mock_runner: MagicMock) -> None:
        mock_runner.run_json.return_value = SAMPLE_PROJECT_LIST_JSON

        projects = await client.list_projects()

        assert len(projects) == 2
        assert projects[0].key == "WNVO"
        assert projects[1].key == "LEARNJIRA"

    async def test_empty_projects(self, client: JiraClient, mock_runner: MagicMock) -> None:
        mock_runner.run_json.return_value = []

        projects = await client.list_projects()
        assert projects == []


class TestListIssueTypes:
    """Tests for JiraClient.list_issue_types()."""

    async def test_list_issue_types(self, client: JiraClient, mock_runner: MagicMock) -> None:
        mock_runner.run_json.return_value = [SAMPLE_ISSUE_JSON]

        types = await client.list_issue_types()

        assert len(types) == 1
        assert types[0].name == "하위 작업"

    async def test_list_issue_types_other_project(self, client: JiraClient, mock_runner: MagicMock) -> None:
        mock_runner.run_json.return_value = [SAMPLE_ISSUE_JSON]

        await client.list_issue_types(project="OTHER")

        call_args = mock_runner.run_json.call_args[0]
        assert "project = OTHER" in call_args


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

    async def test_project_override(self, client: JiraClient, mock_runner: MagicMock) -> None:
        mock_runner.run_json.return_value = SAMPLE_ISSUE_JSON

        await client.create_issue(summary="Task", project="OTHER")

        call_args = mock_runner.run_json.call_args[0]
        assert "OTHER" in call_args

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


class TestAddComment:
    """Tests for JiraClient.add_comment()."""

    async def test_add_comment(self, client: JiraClient, mock_runner: MagicMock) -> None:
        mock_runner.run.return_value = AcliResult(0, "", "")

        await client.add_comment("WNVO-110", body="traceback here")

        call_args = mock_runner.run.call_args[0]
        assert "comment" in call_args
        assert "create" in call_args
        assert "--key" in call_args
        assert "WNVO-110" in call_args
        assert "--body" in call_args
        assert "traceback here" in call_args
