from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .segment import Segment, is_rst
from .seqnum import in_receive_window

CLOSED_STATE = "Closed"


class ResetDisposition(str, Enum):
    ACCEPTED = "Accepted"
    IGNORED = "Ignored"
    NOT_A_RESET = "NotAReset"


@dataclass(frozen=True)
class ResetOutcome:
    """RST ends everything now, with no goodbye - the opposite of teardown.py's patient four packets."""

    disposition: ResetDisposition
    new_state: str
    note: str


def on_reset(state: str, segment: Segment, rcv_nxt: int, window: int) -> ResetOutcome:
    """An in-window RST slams any state straight to CLOSED; an out-of-window RST is just noise."""
    if not is_rst(segment):
        return ResetOutcome(ResetDisposition.NOT_A_RESET, state, "not a reset, nothing to do")

    if in_receive_window(segment.seq, rcv_nxt, max(window, 1)):
        return ResetOutcome(
            ResetDisposition.ACCEPTED,
            CLOSED_STATE,
            "in-window RST: connection is aborted immediately, no reply, no wait",
        )

    # RFC 5961 challenge-ACK behavior is out of scope here; we simply note the drop.
    return ResetOutcome(
        ResetDisposition.IGNORED,
        state,
        "out-of-window RST: ignored (a real stack would send a challenge ACK)",
    )
