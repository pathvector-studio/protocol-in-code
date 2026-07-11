from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .segment import Segment, is_ack, is_fin

TWO_MSL = 240


class CloseState(str, Enum):
    ESTABLISHED = "Established"
    FIN_WAIT_1 = "FinWait1"
    FIN_WAIT_2 = "FinWait2"
    CLOSING = "Closing"
    TIME_WAIT = "TimeWait"
    CLOSE_WAIT = "CloseWait"
    LAST_ACK = "LastAck"
    CLOSED = "Closed"


@dataclass(frozen=True)
class TeardownStep:
    new_state: CloseState
    reply: Segment | None
    note: str
    wait_started_at: int | None = None


def initiate_close(seq: int) -> tuple[CloseState, Segment]:
    """The active closer speaks first too: send FIN, and start waiting for the other three."""
    fin = Segment(seq=seq, ack=0, flags=frozenset({"FIN"}))
    return CloseState.FIN_WAIT_1, fin


def on_segment_active(state: CloseState, segment: Segment, now: int) -> TeardownStep:
    """Goodbye takes four packets (and a wait): the active side tracks its own FIN and the peer's."""
    if state is CloseState.FIN_WAIT_1:
        if is_fin(segment) and is_ack(segment):
            ack = Segment(seq=segment.ack, ack=segment.seq + 1, flags=frozenset({"ACK"}))
            return TeardownStep(CloseState.TIME_WAIT, ack, "peer FIN+ACK, closing now", now)
        if is_ack(segment):
            return TeardownStep(CloseState.FIN_WAIT_2, None, "our FIN acked, waiting for peer's FIN")
        if is_fin(segment):
            # Simultaneous close: both sides sent FIN before hearing the other's ACK.
            ack = Segment(seq=segment.ack, ack=segment.seq + 1, flags=frozenset({"ACK"}))
            return TeardownStep(CloseState.CLOSING, ack, "simultaneous FIN, acked peer's")
        return TeardownStep(state, None, "waiting for ACK of our FIN")

    if state is CloseState.FIN_WAIT_2:
        if is_fin(segment):
            ack = Segment(seq=segment.ack, ack=segment.seq + 1, flags=frozenset({"ACK"}))
            return TeardownStep(CloseState.TIME_WAIT, ack, "peer FIN arrived, entering time-wait", now)
        return TeardownStep(state, None, "waiting for peer's FIN")

    if state is CloseState.CLOSING:
        if is_ack(segment):
            return TeardownStep(CloseState.TIME_WAIT, None, "peer acked our FIN, entering time-wait", now)
        return TeardownStep(state, None, "waiting for ack of our FIN")

    return TeardownStep(state, None, "nothing left to negotiate")


def on_segment_passive(state: CloseState, segment: Segment) -> TeardownStep:
    """The passive closer hears FIN first, and lingers in CLOSE_WAIT until its own app is done."""
    if state is CloseState.ESTABLISHED:
        if is_fin(segment):
            ack = Segment(seq=segment.ack, ack=segment.seq + 1, flags=frozenset({"ACK"}))
            return TeardownStep(CloseState.CLOSE_WAIT, ack, "peer FIN arrived, acked it")
        return TeardownStep(state, None, "connection is open, nothing to close")

    if state is CloseState.CLOSE_WAIT:
        # The passive side's own close() call, not a segment, is what fires this - modeled
        # in the speaker capstone. Here we only describe the wire step: send our own FIN.
        return TeardownStep(state, None, "waiting for local application to call close()")

    if state is CloseState.LAST_ACK:
        if is_ack(segment):
            return TeardownStep(CloseState.CLOSED, None, "peer acked our FIN, fully closed")
        return TeardownStep(state, None, "waiting for ack of our FIN")

    return TeardownStep(state, None, "nothing left to negotiate")


def passive_close(seq: int) -> tuple[CloseState, Segment]:
    """CLOSE_WAIT's own application finally calls close(): send our FIN, await the last ACK."""
    fin = Segment(seq=seq, ack=0, flags=frozenset({"FIN"}))
    return CloseState.LAST_ACK, fin


def time_wait_expired(entered_at: int, now: int) -> bool:
    """TIME_WAIT is patient on purpose: it must outlast any stray segment still crossing the network."""
    return now - entered_at >= TWO_MSL
