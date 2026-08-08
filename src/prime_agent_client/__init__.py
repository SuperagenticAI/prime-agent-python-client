"""Native Python host client for Prime Agent RPC mode."""

from ._version import __version__
from .compatibility import PrimeCompatibility, compatibility_for, parse_version
from .errors import (
    PrimeAgentError,
    PrimeNotStartedError,
    PrimeProcessExited,
    PrimeProtocolError,
    PrimeRequestTimeout,
    PrimeRpcError,
)
from .session import PrimeSession, UIHandler
from .transport import PrimeEventStream, PrimeRpcTransport
from .types import ImageContent, PrimeEvent, PrimeResponse, PrimeVersion

__all__ = [
    "ImageContent",
    "PrimeAgentError",
    "PrimeCompatibility",
    "PrimeEvent",
    "PrimeEventStream",
    "PrimeNotStartedError",
    "PrimeProcessExited",
    "PrimeProtocolError",
    "PrimeRequestTimeout",
    "PrimeResponse",
    "PrimeRpcError",
    "PrimeRpcTransport",
    "PrimeSession",
    "PrimeVersion",
    "UIHandler",
    "compatibility_for",
    "parse_version",
    "__version__",
]
