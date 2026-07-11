"""Refill is lazy.

There is no background process ticking a clock and topping up buckets between requests.
Time debt accrues silently, and the *only* moment it gets settled is when the next request
shows up and asks the bucket a question. This is the same move as read-time expiry in
dns/cache.py: `entry_is_expired(entry, now)` never runs on a schedule either — it runs
exactly once, inline, the moment something asks the cache to look. A token bucket's refill
is that same trick applied to a balance instead of a boolean.

Import layout: this module takes plain scalars (capacity, tokens, rate, timestamps) rather
than a `TokenBucket` object, so it has no dependency on token_bucket.py and reads standalone.
token_bucket.py imports `compute_refill` from here and calls it inside `try_consume`, then
writes the result back onto its own mutable dataclass. Refill is pure math; the dataclass is
just where the math's output gets stored.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RefillResult:
    tokens: float
    last_refill_at: int


def compute_refill(
    tokens: float,
    capacity: float,
    rate_per_sec: float,
    last_refill_at: int,
    now: int,
) -> RefillResult:
    """Elapsed time times rate, capped at capacity, then the clock moves forward.

    Two branches worth naming explicitly:
      - no time passed (now == last_refill_at, or now < last_refill_at): elapsed is zero
        or negative, so the balance is untouched. A request arriving at the same instant
        as the last refill owes nothing new.
      - overflow cap: a bucket idle for a long time accrues more elapsed*rate than it can
        hold. The balance clamps to capacity — unlike a leaky bucket's level, tokens never
        bank credit past the top of the bucket.
    """
    elapsed = now - last_refill_at
    if elapsed <= 0:
        return RefillResult(tokens=tokens, last_refill_at=last_refill_at)

    grown = tokens + elapsed * rate_per_sec
    capped = min(grown, capacity)
    return RefillResult(tokens=capped, last_refill_at=now)


if __name__ == "__main__":
    # Plain growth: 5 seconds at 2/sec adds exactly 10.
    grown = compute_refill(tokens=0, capacity=100, rate_per_sec=2, last_refill_at=0, now=5)
    assert grown.tokens == 10
    assert grown.last_refill_at == 5

    # No time passed: balance and timestamp both untouched.
    still = compute_refill(tokens=10, capacity=100, rate_per_sec=2, last_refill_at=5, now=5)
    assert still.tokens == 10
    assert still.last_refill_at == 5

    # Overflow cap: idle so long the math wants 1000 but the bucket only holds 100.
    capped = compute_refill(tokens=0, capacity=100, rate_per_sec=2, last_refill_at=0, now=500)
    assert capped.tokens == 100
    assert capped.last_refill_at == 500

    print("[OK] refill.py")
