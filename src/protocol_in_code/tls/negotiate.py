from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NegotiationOutcome(str, Enum):
    CHOSEN = "Chosen"
    NO_OVERLAP = "NoOverlap"
    NO_VERSION_OVERLAP = "NoVersionOverlap"


@dataclass(frozen=True)
class NegotiationResult:
    outcome: NegotiationOutcome
    chosen: str | None
    note: str


def choose_version(client_versions: tuple[str, ...], server_preference: tuple[str, ...]) -> NegotiationResult:
    """Agreement is a set intersection: what both sides support, picked in the server's order."""
    overlap = set(client_versions) & set(server_preference)
    if not overlap:
        return NegotiationResult(NegotiationOutcome.NO_VERSION_OVERLAP, None, "no shared version")

    for candidate in server_preference:
        if candidate in overlap:
            return NegotiationResult(NegotiationOutcome.CHOSEN, candidate, f"server prefers {candidate}")

    return NegotiationResult(NegotiationOutcome.NO_VERSION_OVERLAP, None, "no shared version")


def choose_suite(client_suites: tuple[str, ...], server_preference: tuple[str, ...]) -> NegotiationResult:
    """Same rule as the version pick: intersect the two offered sets, then let the server order decide."""
    overlap = set(client_suites) & set(server_preference)
    if not overlap:
        return NegotiationResult(NegotiationOutcome.NO_OVERLAP, None, "no shared cipher suite")

    for candidate in server_preference:
        if candidate in overlap:
            return NegotiationResult(NegotiationOutcome.CHOSEN, candidate, f"server prefers {candidate}")

    return NegotiationResult(NegotiationOutcome.NO_OVERLAP, None, "no shared cipher suite")


def choose_alpn(client_alpn: tuple[str, ...], server_preference: tuple[str, ...]) -> NegotiationResult:
    """ALPN is optional: an empty offer on either side is a clean no-overlap, not an error."""
    overlap = set(client_alpn) & set(server_preference)
    if not overlap:
        return NegotiationResult(NegotiationOutcome.NO_OVERLAP, None, "no shared application protocol")

    for candidate in server_preference:
        if candidate in overlap:
            return NegotiationResult(NegotiationOutcome.CHOSEN, candidate, f"server prefers {candidate}")

    return NegotiationResult(NegotiationOutcome.NO_OVERLAP, None, "no shared application protocol")
