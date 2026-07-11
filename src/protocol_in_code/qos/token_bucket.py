"""A token bucket is two variables.

Everything else — bursts, sustained rate, throttling — falls out of a balance and a
last-touched timestamp. There is no queue, no timer thread, no scheduler. `tokens` says
how much is available right now; `last_refill_at` says when "right now" last got computed.

Contrast with quic/flow_control.py: QUIC's CreditAccount also tracks a balance, but its
credit only ever grows because a receiver explicitly sends a MAX_DATA grant — `grant()` is
the only way `limit` moves, and it never moves on its own. A token bucket's balance grows
on its own, for free, just from time passing; `refill.py` computes that growth. Same shape
(a number that gates whether an action proceeds), opposite source of truth: QUIC's ceiling
is raised by another party, a token bucket's floor rises by the clock.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .refill import compute_refill


class ConsumeOutcome(str, Enum):
    ALLOWED = "Allowed"
    THROTTLED = "Throttled"


@dataclass
class TokenBucket:
    capacity: float
    tokens: float
    rate_per_sec: float
    last_refill_at: int = 0


@dataclass(frozen=True)
class ConsumeResult:
    outcome: ConsumeOutcome
    tokens_remaining: float


def try_consume(bucket: TokenBucket, n: float, now: int) -> ConsumeResult:
    """Refill first, then spend. Refill never runs on its own — this call is what triggers it."""
    refilled = compute_refill(
        tokens=bucket.tokens,
        capacity=bucket.capacity,
        rate_per_sec=bucket.rate_per_sec,
        last_refill_at=bucket.last_refill_at,
        now=now,
    )
    bucket.tokens = refilled.tokens
    bucket.last_refill_at = refilled.last_refill_at

    if bucket.tokens < n:
        return ConsumeResult(ConsumeOutcome.THROTTLED, bucket.tokens)

    bucket.tokens -= n
    return ConsumeResult(ConsumeOutcome.ALLOWED, bucket.tokens)


if __name__ == "__main__":
    bucket = TokenBucket(capacity=10, tokens=10, rate_per_sec=1, last_refill_at=0)

    # A capacity burst at time zero: nothing has refilled yet, but the initial balance
    # already sits at capacity, so a full-capacity request is allowed outright.
    burst = try_consume(bucket, 10, now=0)
    assert burst.outcome is ConsumeOutcome.ALLOWED
    assert bucket.tokens == 0

    # Immediately drained again: no time has passed, so no refill happened.
    drained = try_consume(bucket, 1, now=0)
    assert drained.outcome is ConsumeOutcome.THROTTLED
    assert bucket.tokens == 0

    # 5 seconds later at 1/sec: exactly 5 tokens back, capped nowhere near capacity.
    later = try_consume(bucket, 5, now=5)
    assert later.outcome is ConsumeOutcome.ALLOWED
    assert bucket.tokens == 0

    # Idle for a long stretch: refill caps at capacity, not at the raw elapsed*rate.
    idle = try_consume(bucket, 10, now=1000)
    assert idle.outcome is ConsumeOutcome.ALLOWED
    assert bucket.tokens == 0

    print("[OK] token_bucket.py")
