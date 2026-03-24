"""Tests for input schemas (user-facing request models)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from pyacli.lib.schemas import (
    CreateIssueRequest,
    SearchIssuesRequest,
    TransitionIssueRequest,
)


class TestCreateIssueRequest:
    """Tests for CreateIssueRequest schema."""

    def test_minimal(self) -> None:
        req = CreateIssueRequest(summary="Fix bug")
        args = req.to_acli_args(project="WNVO")

        assert "--project" in args
        assert "WNVO" in args
        assert "--summary" in args
        assert "Fix bug" in args
        assert "--type" in args
        assert "Task" in args
        assert "--json" in args

    def test_all_options(self) -> None:
        req = CreateIssueRequest(
            summary="Fix bug",
            description="Detailed description",
            type="Bug",
            assignee="user@test.com",
            labels=["bug", "backend"],
            parent="WNVO-100",
        )
        args = req.to_acli_args(project="WNVO")

        assert "--description" in args
        assert "Detailed description" in args
        assert "--type" in args
        assert "Bug" in args
        assert "--assignee" in args
        assert "user@test.com" in args
        assert "--label" in args
        assert "bug,backend" in args
        assert "--parent" in args
        assert "WNVO-100" in args

    def test_optional_fields_excluded(self) -> None:
        req = CreateIssueRequest(summary="Simple task")
        args = req.to_acli_args(project="WNVO")

        assert "--description" not in args
        assert "--assignee" not in args
        assert "--label" not in args
        assert "--parent" not in args

    def test_extra_field_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            CreateIssueRequest(summary="Fix", unknown_field="oops")

    def test_issue_type_alias(self) -> None:
        req = CreateIssueRequest(summary="Fix", type="Epic")
        assert req.issue_type == "Epic"


class TestSearchIssuesRequest:
    """Tests for SearchIssuesRequest schema."""

    def test_minimal(self) -> None:
        req = SearchIssuesRequest(jql="project = WNVO")
        args = req.to_acli_args()

        assert "--jql" in args
        assert "project = WNVO" in args
        assert "--limit" in args
        assert "50" in args
        assert "--json" in args

    def test_with_fields(self) -> None:
        req = SearchIssuesRequest(
            jql="project = WNVO",
            limit=10,
            fields="key,summary,status",
        )
        args = req.to_acli_args()

        assert "10" in args
        assert "--fields" in args
        assert "key,summary,status" in args

    def test_extra_field_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            SearchIssuesRequest(jql="project = X", typo_field="oops")


class TestTransitionIssueRequest:
    """Tests for TransitionIssueRequest schema."""

    def test_args(self) -> None:
        req = TransitionIssueRequest(key="WNVO-110", status="Done")
        args = req.to_acli_args()

        assert "--key" in args
        assert "WNVO-110" in args
        assert "--status" in args
        assert "Done" in args
        assert "--yes" in args
        assert "--json" in args

    def test_extra_field_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            TransitionIssueRequest(key="X-1", status="Done", extra="nope")
