from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .candidates import TYPE_PREFERENCE, Candidate

# Pairs are checked in priority order: gathering (candidates.py) produced a
# pile of maybes, and this module turns that pile into an ordered plan and
# then executes it against whatever connectivity actually exists.

# Local preference used to rank candidates within this toy's pairing formula.
# candidates.py's TYPE_PREFERENCE already orders host > reflexive > relayed,
# which is all a single-component toy agent needs to rank its own candidates.
LOCAL_PREF = TYPE_PREFERENCE


def pair_priority(local_prio: int, remote_prio: int, controlling_is_larger: bool = True) -> int:
    """RFC 8445 SS6.1.2.3's min/max form, written out so the asymmetry is visible.

    G = the controlling agent's priority, D = the controlled agent's. The
    formula is 2**32 * MIN(G,D) + 2 * MAX(G,D) + (1 if G > D else 0). Using
    min/max instead of "local" and "remote" directly is what makes both
    agents compute the SAME pair priority for the SAME pair, no matter which
    side is doing the computing - the only thing that differs is who is
    "controlling" for the tie-breaking +1.
    """
    lo = min(local_prio, remote_prio)
    hi = max(local_prio, remote_prio)
    tie_bonus = 1 if controlling_is_larger else 0
    return (2**32) * lo + 2 * hi + tie_bonus


class CheckOutcome(str, Enum):
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"


@dataclass(frozen=True)
class CandidatePair:
    local: Candidate
    remote: Candidate
    priority: int


@dataclass(frozen=True)
class Connectivity:
    """The scenario's ground truth: which (local_type, remote_type) combinations can actually reach each other.

    The caller declares this - it stands in for "what the network topology
    and NAT behaviors actually allow," which nothing in this module can
    derive on its own. ICE does not know NAT personalities; it only finds out
    by checking.
    """

    reachable_type_pairs: frozenset[tuple[str, str]]


def form_checklist(locals_: tuple[Candidate, ...], remotes: tuple[Candidate, ...]) -> tuple[CandidatePair, ...]:
    """Cross every local candidate with every remote one, then sort by priority, highest first - that order IS the plan."""
    pairs = [
        CandidatePair(
            local=local,
            remote=remote,
            priority=pair_priority(LOCAL_PREF[local.ctype], LOCAL_PREF[remote.ctype]),
        )
        for local in locals_
        for remote in remotes
    ]
    return tuple(sorted(pairs, key=lambda p: p.priority, reverse=True))


def check_pair(pair: CandidatePair, reality: Connectivity) -> CheckOutcome:
    """Ask reality, not theory, whether this pair connects - ICE never predicts, it only tests."""
    key = (pair.local.ctype.value, pair.remote.ctype.value)
    if key in reality.reachable_type_pairs:
        return CheckOutcome.SUCCEEDED
    return CheckOutcome.FAILED


@dataclass(frozen=True)
class ChecklistResult:
    nominated: CandidatePair | None
    checked: int


def run_checklist(pairs: tuple[CandidatePair, ...], reality: Connectivity) -> ChecklistResult:
    """Walk the priority-sorted checklist and nominate the first success - aggressive nomination, simplified.

    Real ICE (RFC 8445 SS8) can keep checking after a success and swap the
    nomination later; this toy always stops at the first SUCCEEDED pair,
    which is the simplification real implementations call "aggressive
    nomination."
    """
    for i, pair in enumerate(pairs, start=1):
        if check_pair(pair, reality) is CheckOutcome.SUCCEEDED:
            return ChecklistResult(nominated=pair, checked=i)
    return ChecklistResult(nominated=None, checked=len(pairs))
