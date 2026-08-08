"""Prime Agent release compatibility metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .types import PrimeVersion

SUPPORTED_VERSIONS = frozenset({"0.7.0", "0.7.1"})


@dataclass(frozen=True, slots=True)
class PrimeCompatibility:
    version: PrimeVersion
    tested: bool
    features: frozenset[str]


_CORE_FEATURES = frozenset(
    {
        "prompt",
        "events",
        "abort",
        "steer",
        "follow_up",
        "state",
        "messages",
        "stats",
        "model",
        "compact",
        "refine",
    }
)


def parse_version(output: str) -> PrimeVersion:
    """Extract a semantic version while retaining the original output."""
    raw = output.strip()
    match = re.search(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?!\d)", raw)
    if not match:
        return PrimeVersion(raw=raw)
    major, minor, patch = (int(part) for part in match.groups())
    return PrimeVersion(raw=raw, major=major, minor=minor, patch=patch)


def compatibility_for(version: PrimeVersion) -> PrimeCompatibility:
    normalized = version.normalized
    return PrimeCompatibility(
        version=version,
        tested=normalized in SUPPORTED_VERSIONS,
        features=_CORE_FEATURES,
    )

