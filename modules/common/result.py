"""Shared success/failure result helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class Result(Generic[T]):
    """Structured operation result used by bootstrap and future engines."""

    success: bool
    value: T | None = None
    error_code: str | None = None
    message: str = ""

    @classmethod
    def ok(cls, value: T | None = None, message: str = "ok") -> "Result[T]":
        return cls(success=True, value=value, message=message)

    @classmethod
    def fail(cls, error_code: str, message: str) -> "Result[T]":
        if not error_code:
            raise ValueError("error_code is required for failed results")
        return cls(success=False, error_code=error_code, message=message)


def ok(value: T | None = None, message: str = "ok") -> Result[T]:
    """Create a successful result."""
    return Result.ok(value=value, message=message)


def fail(error_code: str, message: str) -> Result[None]:
    """Create a failed result with a stable error code."""
    return Result.fail(error_code=error_code, message=message)

