"""Three states beat two.

RPKI origin validation, BFD session state, ARP/Neighbor-Discovery state,
and DNSSEC chain validation all refuse to collapse to a boolean. In every
case "no" has two different flavors that call for two different actions,
so the type system carries a third state instead of forcing the caller to
re-derive the distinction from context. This file imports each package's
real enum and states, in the package's own words, what its third value
means operationally.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..arp.cache import NeighborState
from ..dnssec.chain import ChainOutcome
from ..ha.bfd import BfdState
from ..rpki.validate import OriginVerdict


@dataclass(frozen=True)
class TristateDemo:
    protocol: str
    states: tuple[str, str, str]
    third_state_meaning: str


def demonstrate_all() -> tuple[TristateDemo, ...]:
    rows: list[TristateDemo] = []

    # --- RPKI: VALID / INVALID / NOT_FOUND -----------------------------------
    rows.append(
        TristateDemo(
            "rpki",
            (OriginVerdict.VALID.value, OriginVerdict.INVALID.value, OriginVerdict.NOT_FOUND.value),
            "NOT_FOUND: no ROA covers this address range at all - absence of a ROA "
            "is not a denial, it just means nobody published a permission slip.",
        )
    )

    # --- BFD: DOWN / INIT / UP -----------------------------------------------
    rows.append(
        TristateDemo(
            "bfd",
            (BfdState.DOWN.value, BfdState.INIT.value, BfdState.UP.value),
            "INIT: half-agreed - the local side is negotiating and has heard the "
            "remote side is trying too, but the two ends have not yet confirmed "
            "the session together.",
        )
    )

    # --- ARP / Neighbor Discovery: INCOMPLETE / REACHABLE / STALE -----------
    rows.append(
        TristateDemo(
            "arp",
            (NeighborState.INCOMPLETE.value, NeighborState.REACHABLE.value, NeighborState.STALE.value),
            "STALE: usable but doubted - the mapping is still forwarded on, but it "
            "has outlived its confidence window and needs re-confirmation.",
        )
    )

    # --- DNSSEC: SECURE / BOGUS* (collapsed) / INSECURE -----------------------
    # ChainOutcome actually has three BOGUS_* flavors (BOGUS_RECORD_SIG,
    # BOGUS_KEY_SIG, BOGUS_DS_MISMATCH) distinguishing WHERE the chain broke.
    # For this three-state comparison they collapse to one "BOGUS" bucket -
    # each is still a proof that failed, just at a different hop.
    bogus_values = (
        ChainOutcome.BOGUS_RECORD_SIG.value,
        ChainOutcome.BOGUS_KEY_SIG.value,
        ChainOutcome.BOGUS_DS_MISMATCH.value,
    )
    rows.append(
        TristateDemo(
            "dnssec",
            (ChainOutcome.SECURE.value, "Bogus (" + "/".join(bogus_values) + ")", ChainOutcome.INSECURE.value),
            "INSECURE: provably unsigned - a parent zone has no DS record for its "
            "child at all, which is a proven absence of a signature chain, not a "
            "broken proof like BOGUS is.",
        )
    )

    return tuple(rows)


def why_not_bool() -> str:
    """The shared lesson across all four tri-states.

    In every case the third state exists because "no" has two different
    flavors that demand different actions: RPKI's NOT_FOUND is not INVALID,
    BFD's INIT is not DOWN, ARP's STALE is not gone, and DNSSEC's INSECURE
    is not BOGUS. A boolean would force the caller to conflate "actively
    rejected" with "no information exists," and those two situations call
    for opposite responses - reject the route versus fall back to
    unauthenticated trust, tear down the session versus keep negotiating,
    evict the neighbor versus keep forwarding while re-confirming.
    """
    return (
        "Every one of these protocols needed a third state because 'no' has two "
        "different flavors - an active, proven rejection versus a mere absence of "
        "proof - and those two flavors demand different actions from the caller, "
        "so collapsing them into one boolean would silently pick the wrong response."
    )
