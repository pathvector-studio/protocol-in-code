from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Matching rules follow RFC 6125 SS6.4.3: a wildcard covers only the leftmost whole
# label, and never spans a label boundary or shares a label with other characters.


class HostnameVerdict(str, Enum):
    MATCHED_EXACT = "MatchedExact"
    MATCHED_WILDCARD = "MatchedWildcard"
    NO_MATCH = "NoMatch"


@dataclass(frozen=True)
class HostnameMatch:
    verdict: HostnameVerdict
    matched_san: str | None


def matches_exact(hostname: str, san: str) -> bool:
    """A cert is for a name, not a server: the plainest case is a literal, case-insensitive equal."""
    return hostname.lower() == san.lower()


def matches_wildcard(hostname: str, san: str) -> bool:
    """The wildcard must be the whole leftmost label - `*.example.com`, never `w*.example.com`."""
    san = san.lower()
    hostname = hostname.lower()

    if not san.startswith("*."):
        return False

    wildcard_suffix = san[1:]  # keeps the leading dot, e.g. ".example.com"
    if not hostname.endswith(wildcard_suffix):
        return False

    remaining = hostname[: -len(wildcard_suffix)]
    # The label matched by "*" must be non-empty and contain no further dots,
    # so "a.b.example.com" and "example.com" are both rejected.
    return len(remaining) > 0 and "." not in remaining


def match_hostname(hostname: str, san_names: tuple[str, ...]) -> HostnameMatch:
    """Check the exact names first, then wildcards - either way, one SAN must own the name."""
    for san in san_names:
        if matches_exact(hostname, san):
            return HostnameMatch(HostnameVerdict.MATCHED_EXACT, san)

    for san in san_names:
        if matches_wildcard(hostname, san):
            return HostnameMatch(HostnameVerdict.MATCHED_WILDCARD, san)

    return HostnameMatch(HostnameVerdict.NO_MATCH, None)
