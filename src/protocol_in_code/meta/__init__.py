"""Same shape, different protocol.

The course finale: comparative code, not a new protocol. Each file here
imports real functions from many of the packages built up over the course
and runs them side by side, making the recurring structures - the
expiring dict, election-by-comparison, the tri-state verdict,
silence-means-failure, and the event loop itself - explicit instead of
merely implied by repetition.
"""

from __future__ import annotations

from .election import ElectionDemo, demonstrate_all as election_demonstrate_all, the_inversion
from .expiring_state import ExpiryDemo, common_shape, demonstrate_all as expiring_state_demonstrate_all
from .silence import SilenceDemo, demonstrate_all as silence_demonstrate_all, timescale_spread
from .the_loop import (
    LoopSummary,
    common_skeleton,
    run_two_loops_side_by_side,
    survey,
)
from .tristate import TristateDemo, demonstrate_all as tristate_demonstrate_all, why_not_bool

__all__ = [
    "ElectionDemo",
    "ExpiryDemo",
    "LoopSummary",
    "SilenceDemo",
    "TristateDemo",
    "common_shape",
    "common_skeleton",
    "election_demonstrate_all",
    "expiring_state_demonstrate_all",
    "run_two_loops_side_by_side",
    "silence_demonstrate_all",
    "survey",
    "the_inversion",
    "timescale_spread",
    "tristate_demonstrate_all",
    "why_not_bool",
]
