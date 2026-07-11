from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# RFC 5681: TCP Congestion Control. cwnd and ssthresh are counted in MSS units throughout.
INITIAL_CWND = 1


class CongestionPhase(str, Enum):
    SLOW_START = "SlowStart"
    CONGESTION_AVOIDANCE = "CongestionAvoidance"


@dataclass
class CongestionState:
    """cwnd is just a variable: every branch below is a rule for how one integer moves."""

    cwnd: int = INITIAL_CWND
    ssthresh: int = 64
    acks_in_round: int = 0


def phase(state: CongestionState) -> CongestionPhase:
    if state.cwnd < state.ssthresh:
        return CongestionPhase.SLOW_START
    return CongestionPhase.CONGESTION_AVOIDANCE


def on_ack(state: CongestionState) -> CongestionPhase:
    """Slow start doubles cwnd per round trip (one MSS per ack); avoidance adds one MSS per round trip."""
    current_phase = phase(state)

    if current_phase is CongestionPhase.SLOW_START:
        state.cwnd += 1
        state.acks_in_round = 0
        return current_phase

    # Congestion avoidance: only after a full cwnd's worth of acks do we grow by one MSS.
    state.acks_in_round += 1
    if state.acks_in_round >= state.cwnd:
        state.cwnd += 1
        state.acks_in_round = 0
    return current_phase


def on_timeout(state: CongestionState) -> None:
    """A timeout means the network is more congested than we assumed: halve, then restart small."""
    state.ssthresh = max(state.cwnd // 2, 2)
    state.cwnd = INITIAL_CWND
    state.acks_in_round = 0


def on_fast_retransmit(state: CongestionState) -> None:
    """Fast recovery (simplified): halve ssthresh, but resume right at that new ceiling, not from 1."""
    state.ssthresh = max(state.cwnd // 2, 2)
    state.cwnd = state.ssthresh
    state.acks_in_round = 0
