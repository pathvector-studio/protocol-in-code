from __future__ import annotations

from dataclasses import dataclass

# RFC 6298: Computing TCP's Retransmission Timer.
MIN_RTO_MS = 1_000
MAX_RTO_MS = 60_000


@dataclass
class RttEstimator:
    srtt: float | None = None
    rttvar: float = 0.0


def observe(estimator: RttEstimator, sample_ms: float) -> None:
    """The timer learns the network: each RTT sample nudges a smoothed estimate, Jacobson/Karels style."""
    if estimator.srtt is None:
        # RFC 6298 2.2: first measurement seeds srtt directly, rttvar to half of it.
        estimator.srtt = sample_ms
        estimator.rttvar = sample_ms / 2
        return

    # RFC 6298 2.3: rttvar tracks how much the sample disagreed with the running estimate.
    estimator.rttvar = 0.75 * estimator.rttvar + 0.25 * abs(estimator.srtt - sample_ms)
    estimator.srtt = 0.875 * estimator.srtt + 0.125 * sample_ms


def rto(estimator: RttEstimator) -> int:
    """RTO = srtt + 4*rttvar, clamped so the timer is never absurdly tight or absurdly loose."""
    if estimator.srtt is None:
        return MIN_RTO_MS

    computed = estimator.srtt + 4 * estimator.rttvar
    return int(min(MAX_RTO_MS, max(MIN_RTO_MS, computed)))


def on_timeout(current_rto_ms: int) -> int:
    """RFC 6298 5.5: back off exponentially on every consecutive timeout, capped at MAX_RTO."""
    return min(MAX_RTO_MS, current_rto_ms * 2)
