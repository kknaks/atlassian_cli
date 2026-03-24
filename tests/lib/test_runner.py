"""Tests for AcliRunner subprocess wrapper."""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pyacli.lib.exceptions import (
    AcliAuthError,
    AcliError,
    AcliNotFoundError,
    AcliTimeoutError,
)
from pyacli.lib.runner import AcliResult, AcliRunner


def _make_process(
    return_code: int = 0,
    stdout: str = "",
    stderr: str = "",
) -> MagicMock:
    """Create a mock async subprocess."""
    proc = MagicMock()
    proc.returncode = return_code
    proc.communicate = AsyncMock(
        return_value=(stdout.encode(), stderr.encode()),
    )
    proc.kill = MagicMock()
    return proc


class TestExec:
    """Tests for AcliRunner._exec()."""

    async def test_acli_not_found(self) -> None:
        runner = AcliRunner(acli_path=None)
        runner._acli_path = None
        with pytest.raises(AcliNotFoundError):
            await runner._exec("jira", "auth", "status")

    @patch("pyacli.lib.runner.asyncio.create_subprocess_exec")
    async def test_successful_exec(self, mock_exec: AsyncMock) -> None:
        proc = _make_process(return_code=0, stdout="ok")
        mock_exec.return_value = proc

        runner = AcliRunner(acli_path="/usr/bin/acli")
        result = await runner._exec("jira", "auth", "status")

        assert result.return_code == 0
        assert result.stdout == "ok"
        mock_exec.assert_called_once()

    @patch("pyacli.lib.runner.asyncio.create_subprocess_exec")
    async def test_timeout(self, mock_exec: AsyncMock) -> None:
        proc = MagicMock()
        proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError)
        proc.kill = MagicMock()
        mock_exec.return_value = proc

        runner = AcliRunner(acli_path="/usr/bin/acli", timeout=1.0)
        with pytest.raises(AcliTimeoutError, match="timed out"):
            await runner._exec("jira", "workitem", "search")


class TestEnsureAuth:
    """Tests for AcliRunner._ensure_auth()."""

    async def test_skip_if_already_authenticated(self) -> None:
        runner = AcliRunner(acli_path="/usr/bin/acli")
        runner._authenticated = True
        await runner._ensure_auth()  # should not raise

    @patch("pyacli.lib.runner.asyncio.create_subprocess_exec")
    async def test_auth_status_ok(self, mock_exec: AsyncMock) -> None:
        proc = _make_process(return_code=0, stdout="✓ Authenticated")
        mock_exec.return_value = proc

        runner = AcliRunner(acli_path="/usr/bin/acli")
        await runner._ensure_auth()

        assert runner._authenticated is True

    @patch("pyacli.lib.runner.asyncio.create_subprocess_exec")
    async def test_missing_env_vars(self, mock_exec: AsyncMock) -> None:
        proc = _make_process(return_code=1, stderr="unauthorized")
        mock_exec.return_value = proc

        runner = AcliRunner(acli_path="/usr/bin/acli")

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(AcliAuthError, match="Missing credentials"):
                await runner._ensure_auth()

    @patch("pyacli.lib.runner.asyncio.create_subprocess_exec")
    async def test_auto_login_success(self, mock_exec: AsyncMock) -> None:
        # First call: auth status fails
        status_proc = _make_process(return_code=1, stderr="unauthorized")
        # Second call: login succeeds
        login_proc = _make_process(return_code=0, stdout="logged in")

        mock_exec.side_effect = [status_proc, login_proc]

        runner = AcliRunner(acli_path="/usr/bin/acli")

        env = {
            "ATLASSIAN_SITE": "test.atlassian.net",
            "ATLASSIAN_EMAIL": "user@test.com",
            "ATLASSIAN_API_TOKEN": "secret-token",
        }
        with patch.dict("os.environ", env):
            await runner._ensure_auth()

        assert runner._authenticated is True

    @patch("pyacli.lib.runner.asyncio.create_subprocess_exec")
    async def test_auto_login_failure(self, mock_exec: AsyncMock) -> None:
        status_proc = _make_process(return_code=1, stderr="unauthorized")
        login_proc = _make_process(return_code=1, stderr="invalid token")

        mock_exec.side_effect = [status_proc, login_proc]

        runner = AcliRunner(acli_path="/usr/bin/acli")

        env = {
            "ATLASSIAN_SITE": "test.atlassian.net",
            "ATLASSIAN_EMAIL": "user@test.com",
            "ATLASSIAN_API_TOKEN": "bad-token",
        }
        with patch.dict("os.environ", env):
            with pytest.raises(AcliAuthError, match="Login failed"):
                await runner._ensure_auth()


class TestRun:
    """Tests for AcliRunner.run()."""

    @patch.object(AcliRunner, "_ensure_auth", new_callable=AsyncMock)
    @patch.object(AcliRunner, "_exec", new_callable=AsyncMock)
    async def test_successful_run(
        self, mock_exec: AsyncMock, mock_auth: AsyncMock,
    ) -> None:
        mock_exec.return_value = AcliResult(0, "output", "")

        runner = AcliRunner(acli_path="/usr/bin/acli")
        result = await runner.run("jira", "workitem", "view", "WNVO-110")

        assert result.stdout == "output"
        mock_auth.assert_awaited_once()
        mock_exec.assert_awaited_once()

    @patch.object(AcliRunner, "_ensure_auth", new_callable=AsyncMock)
    @patch.object(AcliRunner, "_exec", new_callable=AsyncMock)
    async def test_command_failure(
        self, mock_exec: AsyncMock, mock_auth: AsyncMock,
    ) -> None:
        mock_exec.return_value = AcliResult(1, "", "something went wrong")

        runner = AcliRunner(acli_path="/usr/bin/acli")
        with pytest.raises(AcliError, match="something went wrong"):
            await runner.run("jira", "workitem", "view", "BAD-1")

    @patch.object(AcliRunner, "_ensure_auth", new_callable=AsyncMock)
    @patch.object(AcliRunner, "_exec", new_callable=AsyncMock)
    async def test_401_retry_success(
        self, mock_exec: AsyncMock, mock_auth: AsyncMock,
    ) -> None:
        # First call fails with 401, second succeeds after re-auth
        mock_exec.side_effect = [
            AcliResult(1, "", "unauthorized"),
            AcliResult(0, "ok", ""),
        ]

        runner = AcliRunner(acli_path="/usr/bin/acli")
        result = await runner.run("jira", "workitem", "view", "WNVO-110")

        assert result.stdout == "ok"
        assert mock_auth.await_count == 2  # initial + retry
        assert mock_exec.await_count == 2

    @patch.object(AcliRunner, "_ensure_auth", new_callable=AsyncMock)
    @patch.object(AcliRunner, "_exec", new_callable=AsyncMock)
    async def test_401_retry_failure(
        self, mock_exec: AsyncMock, mock_auth: AsyncMock,
    ) -> None:
        mock_exec.side_effect = [
            AcliResult(1, "", "unauthorized"),
            AcliResult(1, "", "still unauthorized"),
        ]

        runner = AcliRunner(acli_path="/usr/bin/acli")
        with pytest.raises(AcliError, match="failed after re-auth"):
            await runner.run("jira", "workitem", "view", "WNVO-110")


class TestRunJson:
    """Tests for AcliRunner.run_json()."""

    @patch.object(AcliRunner, "run", new_callable=AsyncMock)
    async def test_parse_dict(self, mock_run: AsyncMock) -> None:
        mock_run.return_value = AcliResult(0, '{"key": "WNVO-110"}', "")

        runner = AcliRunner(acli_path="/usr/bin/acli")
        data = await runner.run_json("jira", "workitem", "view", "WNVO-110", "--json")

        assert data == {"key": "WNVO-110"}

    @patch.object(AcliRunner, "run", new_callable=AsyncMock)
    async def test_parse_list(self, mock_run: AsyncMock) -> None:
        mock_run.return_value = AcliResult(0, '[{"key": "WNVO-1"}]', "")

        runner = AcliRunner(acli_path="/usr/bin/acli")
        data = await runner.run_json("jira", "workitem", "search", "--json")

        assert isinstance(data, list)
        assert len(data) == 1

    @patch.object(AcliRunner, "run", new_callable=AsyncMock)
    async def test_invalid_json(self, mock_run: AsyncMock) -> None:
        mock_run.return_value = AcliResult(0, "not json", "")

        runner = AcliRunner(acli_path="/usr/bin/acli")
        with pytest.raises(AcliError, match="JSON parse error"):
            await runner.run_json("jira", "workitem", "view", "--json")
