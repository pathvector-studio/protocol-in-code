from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .segment import Segment, is_ack, is_syn


class ConnectionState(str, Enum):
    CLOSED = "Closed"
    LISTEN = "Listen"
    SYN_SENT = "SynSent"
    SYN_RCVD = "SynRcvd"
    ESTABLISHED = "Established"


@dataclass(frozen=True)
class HandshakeStep:
    new_state: ConnectionState
    reply: Segment | None
    note: str


def active_open(iss: int) -> tuple[ConnectionState, Segment]:
    """The client speaks first: send SYN, and wait."""
    syn = Segment(seq=iss, ack=0, flags=frozenset({"SYN"}))
    return ConnectionState.SYN_SENT, syn


def on_segment(state: ConnectionState, segment: Segment, iss: int) -> HandshakeStep:
    """It takes three packets to say hello: SYN, SYN+ACK, ACK - each a state transition."""

    # --- passive-open path: a listener hears a SYN and answers with its own ---
    if state is ConnectionState.LISTEN:
        if is_syn(segment):
            syn_ack = Segment(
                seq=iss,
                ack=segment.seq + 1,
                flags=frozenset({"SYN", "ACK"}),
            )
            return HandshakeStep(ConnectionState.SYN_RCVD, syn_ack, "heard SYN, sent SYN+ACK")
        return HandshakeStep(state, None, "listening, nothing to do yet")

    if state is ConnectionState.SYN_RCVD:
        if is_ack(segment) and not is_syn(segment):
            return HandshakeStep(ConnectionState.ESTABLISHED, None, "heard final ACK, established")
        return HandshakeStep(state, None, "still waiting for the final ACK")

    # --- active-open path: the initiator hears SYN+ACK and closes the loop ---
    if state is ConnectionState.SYN_SENT:
        if is_syn(segment) and is_ack(segment):
            final_ack = Segment(
                seq=segment.ack,
                ack=segment.seq + 1,
                flags=frozenset({"ACK"}),
            )
            return HandshakeStep(ConnectionState.ESTABLISHED, final_ack, "heard SYN+ACK, sent final ACK")
        if is_syn(segment):
            # Simultaneous open: both sides opened at once. Not this course's focus.
            return HandshakeStep(state, None, "heard bare SYN while syn-sent, ignoring")
        return HandshakeStep(state, None, "waiting for SYN+ACK")

    if state is ConnectionState.ESTABLISHED:
        return HandshakeStep(state, None, "already established, handshake is over")

    return HandshakeStep(state, None, "closed, nothing to negotiate")
