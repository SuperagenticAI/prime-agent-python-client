"""Exceptions raised by the Prime Agent Python client."""

from __future__ import annotations

from typing import Any


class PrimeAgentError(Exception):
    """Base exception for the client package."""


class PrimeNotStartedError(PrimeAgentError):
    """Raised when an RPC operation is attempted before startup."""


class PrimeProtocolError(PrimeAgentError):
    """Raised when Prime Agent emits an invalid protocol record."""


class PrimeRequestTimeout(PrimeAgentError):
    """Raised when an RPC response does not arrive before its deadline."""

    def __init__(self, command: str, timeout: float, stderr: str = "") -> None:
        detail = f"Prime Agent RPC request {command!r} timed out after {timeout:.1f}s"
        if stderr:
            detail += f". Recent stderr: {stderr}"
        super().__init__(detail)
        self.command = command
        self.timeout = timeout
        self.stderr = stderr


class PrimeRpcError(PrimeAgentError):
    """A command was understood by the RPC server but failed."""

    def __init__(self, command: str, message: str, response: dict[str, Any]) -> None:
        super().__init__(f"Prime Agent RPC {command!r} failed: {message}")
        self.command = command
        self.message = message
        self.response = response


class PrimeProcessExited(PrimeAgentError):
    """The Prime Agent subprocess exited while the client was active."""

    def __init__(self, returncode: int | None, stderr: str = "") -> None:
        detail = f"Prime Agent process exited with code {returncode}"
        if stderr:
            detail += f". Recent stderr: {stderr}"
        super().__init__(detail)
        self.returncode = returncode
        self.stderr = stderr
