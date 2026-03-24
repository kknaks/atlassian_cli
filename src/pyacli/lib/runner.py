"""Subprocess wrapper for acli CLI binary."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
from dataclasses import dataclass

from pyacli.lib.exceptions import (
    AcliAuthError,
    AcliError,
    AcliNotFoundError,
    AcliTimeoutError,
)

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0


@dataclass(frozen=True)
class AcliResult:
    """Raw result from an acli command execution."""

    return_code: int
    stdout: str
    stderr: str


class AcliRunner:
    """Executes acli CLI commands via async subprocess."""

    def __init__(
        self,
        acli_path: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._acli_path = acli_path or shutil.which("acli")
        self._timeout = timeout
        self._authenticated = False

    async def _ensure_auth(self) -> None:
        """Auto-login using environment variables. Skip if already authenticated."""
        if self._authenticated:
            return

        result = await self._exec("jira", "auth", "status")
        if result.return_code == 0 and "authenticated" in result.stdout.lower():
            self._authenticated = True
            return

        site = os.environ.get("ATLASSIAN_SITE")
        email = os.environ.get("ATLASSIAN_EMAIL")
        token = os.environ.get("ATLASSIAN_API_TOKEN")

        if not all([site, email, token]):
            raise AcliAuthError(
                "Missing credentials. Set ATLASSIAN_SITE, ATLASSIAN_EMAIL, "
                "ATLASSIAN_API_TOKEN or run 'acli jira auth login --web'."
            )

        if not self._acli_path:
            raise AcliNotFoundError(
                "acli binary not found. "
                "Install: brew tap atlassian/homebrew-acli && brew install acli"
            )

        logger.debug("Attempting auto-login for site=%s email=%s", site, email)

        proc = await asyncio.create_subprocess_exec(
            self._acli_path, "jira", "auth", "login",
            "--site", site,
            "--email", email,
            "--token",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await proc.communicate(
            input=token.encode(),
        )

        if proc.returncode != 0:
            raise AcliAuthError(
                f"Login failed: {stderr_bytes.decode().strip()}"
            )

        logger.debug("Auto-login successful")
        self._authenticated = True

    async def _exec(self, *args: str) -> AcliResult:
        """Execute acli binary directly without auth check."""
        if not self._acli_path:
            raise AcliNotFoundError(
                "acli binary not found. "
                "Install: brew tap atlassian/homebrew-acli && brew install acli"
            )

        logger.debug("Executing: acli %s", " ".join(args))

        proc = await asyncio.create_subprocess_exec(
            self._acli_path, *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            proc.kill()
            raise AcliTimeoutError(
                f"Command timed out after {self._timeout}s: acli {' '.join(args)}"
            )

        result = AcliResult(
            return_code=proc.returncode,
            stdout=stdout_bytes.decode(),
            stderr=stderr_bytes.decode(),
        )

        logger.debug(
            "Result: return_code=%d stdout=%s stderr=%s",
            result.return_code,
            result.stdout[:200],
            result.stderr[:200],
        )

        return result

    async def run(self, *args: str) -> AcliResult:
        """Execute acli command with auth check and 401 retry."""
        await self._ensure_auth()
        result = await self._exec(*args)

        if result.return_code != 0:
            stderr = result.stderr.strip()

            if "unauthorized" in stderr.lower() or "401" in stderr:
                logger.warning("Auth expired, retrying login")
                self._authenticated = False
                await self._ensure_auth()
                result = await self._exec(*args)

                if result.return_code != 0:
                    raise AcliError(
                        f"Command failed after re-auth: {result.stderr.strip()}"
                    )
            else:
                raise AcliError(f"Command failed: {stderr}")

        return result

    async def run_json(self, *args: str) -> dict | list:
        """Execute acli command and parse JSON output."""
        result = await self.run(*args)

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise AcliError(
                f"JSON parse error: {exc}\nstdout: {result.stdout[:500]}"
            ) from exc
