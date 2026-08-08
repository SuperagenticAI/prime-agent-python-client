"""Open, forward-compatible types for Prime Agent's RPC protocol."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, TypedDict

JsonObject = dict[str, Any]


class ImageContent(TypedDict):
    type: str
    data: str
    mimeType: str


@dataclass(frozen=True, slots=True)
class PrimeEvent:
    """One unsolicited RPC event.

    ``raw`` intentionally preserves fields unknown to this client version.
    Prime Agent's event schema evolves faster than the command surface, so
    discarding unfamiliar data would make the compatibility layer brittle.
    """

    type: str
    raw: Mapping[str, Any]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> PrimeEvent:
        copied = dict(payload)
        return cls(type=str(copied.get("type") or "unknown"), raw=MappingProxyType(copied))

    def get(self, key: str, default: Any = None) -> Any:
        return self.raw.get(key, default)


@dataclass(frozen=True, slots=True)
class PrimeResponse:
    """Successful RPC response with its unmodified wire payload."""

    id: str
    command: str
    data: Any = None
    raw: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PrimeVersion:
    """Version reported by the public ``prime-agent`` executable."""

    raw: str
    major: int | None = None
    minor: int | None = None
    patch: int | None = None

    @property
    def normalized(self) -> str | None:
        if self.major is None or self.minor is None or self.patch is None:
            return None
        return f"{self.major}.{self.minor}.{self.patch}"

