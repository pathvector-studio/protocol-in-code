"""Stratum is depth in a tree.

Stratum 1 servers hang off a reference clock (GPS, an atomic standard).
Everyone else's stratum is one more than whoever they sync from -- the same
hop-count arithmetic as RIP's metric (see rip/update.py: `advertised_metric
+ 1`), just counting distance from a clock instead of distance from a
prefix's origin. RFC 5905 section 7.3 reserves 16 as "unsynchronized": a
server that has not (yet, or ever) locked onto a working source.
"""

from __future__ import annotations

from dataclasses import dataclass

STRATUM_REFERENCE = 1
STRATUM_MAX = 15
STRATUM_UNSYNC = 16


@dataclass(frozen=True)
class Candidate:
    server: str
    stratum: int
    delay_ms: float


def advertised_stratum(upstream_stratum: int) -> int:
    """A server tells its clients upstream_stratum + 1 -- visible one-hop
    growth, exactly like RIP incrementing a metric by one per router. Capped
    at STRATUM_UNSYNC: you cannot advertise a worse number than "not synced".
    """
    return min(upstream_stratum + 1, STRATUM_UNSYNC)


def usable(candidate: Candidate) -> bool:
    """Stratum 16 means unsynchronized; anything from STRATUM_REFERENCE
    through STRATUM_MAX is a real, usable time source.
    """
    return STRATUM_REFERENCE <= candidate.stratum <= STRATUM_MAX


def prefer(a: Candidate, b: Candidate) -> Candidate:
    """Lower stratum wins -- fewer hops from the reference clock means less
    accumulated error. A tie in stratum falls back to lower delay, since a
    shorter round trip bounds the uncertainty in the offset estimate tighter
    (see offset.py's derivation: delay does not appear in theta directly,
    but a smaller delay means less room for the symmetry assumption to be
    wrong in practice).
    """
    if a.stratum != b.stratum:
        return a if a.stratum < b.stratum else b
    return a if a.delay_ms <= b.delay_ms else b
