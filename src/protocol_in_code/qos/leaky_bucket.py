"""Leaky and token are cousins.

Same two variables — a balance and a last-touched timestamp — same lazy-refill trick from
refill.py, run in the opposite direction. A token bucket's balance is "credit available";
a leaky bucket's `level` is "backlog waiting to drain." Arrivals ADD to the level instead of
subtracting from a balance; the passage of time SUBTRACTS (leaks) instead of adding.
Whatever doesn't fit when the level is already at capacity is dropped outright, not queued.

    token bucket                          leaky bucket
    ---------------------------------     ---------------------------------
    tokens start full, drain on use       level starts empty, fills on arrival
    time ADDS tokens back                 time SUBTRACTS (drains) the level
    a burst up to capacity passes at      a burst is smoothed: only leak_per_sec
      once, instantly                       worth of "room" opens up per second
    rejection = insufficient balance      rejection = OVERFLOWED, backlog too full
    permits bursts up to capacity         smooths output to a steady rate

Same skeleton, opposite temperament: token bucket is permissive about bursts and strict
about the average; leaky bucket is strict about bursts and only ever emits at leak_per_sec.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OfferOutcome(str, Enum):
    ACCEPTED = "Accepted"
    OVERFLOWED = "Overflowed"


@dataclass
class LeakyBucket:
    capacity: float
    level: float
    leak_per_sec: float
    last_leak_at: int = 0


@dataclass(frozen=True)
class OfferResult:
    outcome: OfferOutcome
    level: float


def leak(bucket: LeakyBucket, now: int) -> None:
    """Elapsed time times leak rate comes OFF the level, floored at zero — the mirror of refill."""
    elapsed = now - bucket.last_leak_at
    if elapsed <= 0:
        return

    drained = bucket.level - elapsed * bucket.leak_per_sec
    bucket.level = max(drained, 0)
    bucket.last_leak_at = now


def offer(bucket: LeakyBucket, n: float, now: int) -> OfferResult:
    """Leak first, then try to add. Whatever doesn't fit over capacity is dropped, not queued."""
    leak(bucket, now)

    if bucket.level + n > bucket.capacity:
        return OfferResult(OfferOutcome.OVERFLOWED, bucket.level)

    bucket.level += n
    return OfferResult(OfferOutcome.ACCEPTED, bucket.level)


if __name__ == "__main__":
    bucket = LeakyBucket(capacity=10, level=0, leak_per_sec=1, last_leak_at=0)

    # Fill to capacity at time zero.
    filled = offer(bucket, 10, now=0)
    assert filled.outcome is OfferOutcome.ACCEPTED
    assert bucket.level == 10

    # Immediately offer more: no time has passed, nothing has drained, this overflows.
    overflowed = offer(bucket, 1, now=0)
    assert overflowed.outcome is OfferOutcome.OVERFLOWED
    assert bucket.level == 10  # the drop changes nothing about the existing backlog

    # 5 seconds later at 1/sec: 5 units of room opened up, so 5 more fits exactly.
    later = offer(bucket, 5, now=5)
    assert later.outcome is OfferOutcome.ACCEPTED
    assert bucket.level == 10

    # Side-by-side with token_bucket.py: a token bucket allows a full-capacity burst
    # arriving all at once (see try_consume's first assertion). A leaky bucket, given
    # the exact same burst size against an already-full level, drops it — that's the
    # smoothing: it will only ever accept leak_per_sec worth of new arrivals per second,
    # no matter how empty the "credit" would look under token-bucket accounting.
    fresh = LeakyBucket(capacity=10, level=10, leak_per_sec=1, last_leak_at=0)
    burst_rejected = offer(fresh, 10, now=0)
    assert burst_rejected.outcome is OfferOutcome.OVERFLOWED

    print("[OK] leaky_bucket.py")
