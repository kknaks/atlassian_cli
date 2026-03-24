"""Tests for pyacli exception hierarchy."""
from __future__ import annotations

import pytest

from pyacli.lib.exceptions import (
    AcliAuthError,
    AcliError,
    AcliNotFoundError,
    AcliTimeoutError,
    AcliValidationError,
)


class TestExceptionHierarchy:
    """All custom exceptions must inherit from AcliError."""

    @pytest.mark.parametrize(
        "exc_class",
        [AcliNotFoundError, AcliAuthError, AcliTimeoutError, AcliValidationError],
    )
    def test_inherits_from_acli_error(self, exc_class: type[AcliError]) -> None:
        assert issubclass(exc_class, AcliError)

    @pytest.mark.parametrize(
        "exc_class",
        [AcliError, AcliNotFoundError, AcliAuthError, AcliTimeoutError, AcliValidationError],
    )
    def test_inherits_from_exception(self, exc_class: type[Exception]) -> None:
        assert issubclass(exc_class, Exception)

    def test_catch_all_with_acli_error(self) -> None:
        """Catching AcliError should catch all subtypes."""
        for exc_class in [AcliNotFoundError, AcliAuthError, AcliTimeoutError, AcliValidationError]:
            with pytest.raises(AcliError):
                raise exc_class("test message")

    def test_exception_message(self) -> None:
        err = AcliAuthError("token expired")
        assert str(err) == "token expired"
