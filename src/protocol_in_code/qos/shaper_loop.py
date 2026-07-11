"""Build the toy shaper loop.

Everything upstream in this track is a standalone mechanism: a token bucket refills
itself, a leaky bucket drains itself, a class tree validates its own shape. A shaper
is just those mechanisms wired together — classify a packet into a class, then ask that
class's own bucket whether it fits. There is no new algorithm here, only assembly.

The headline this loop exists to demonstrate is isolation: one class exhausting its
bucket must not affect another class's bucket, because each class owns an independent
TokenBucket keyed by name. run_contention below drives exactly that scenario, plus a
side-by-side of the same burst under a token bucket (passes) versus what a leaky bucket
would have done to it (smoothed/dropped) - tying back to leaky_bucket.py's comparison
table.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .classes import ClassTree
from .leaky_bucket import LeakyBucket, OfferOutcome, offer
from .token_bucket import ConsumeOutcome, TokenBucket, try_consume


@dataclass(frozen=True)
class EnqueueResult:
    class_name: str
    outcome: ConsumeOutcome
    tokens_remaining: float


@dataclass
class ToyShaper:
    """One TokenBucket per traffic class, a tree describing how the classes relate, a clock."""

    tree: ClassTree
    buckets: dict[str, TokenBucket] = field(default_factory=dict)
    clock: int = 0
    trace: list[str] = field(default_factory=list)

    def tick(self, seconds: int) -> None:
        self.clock += seconds

    def enqueue(self, class_name: str, size: float, now: int) -> EnqueueResult:
        """Classify by name, then spend against that class's own bucket - nothing shared."""
        bucket = self.buckets[class_name]
        consumed = try_consume(bucket, size, now)
        self.trace.append(
            f"enqueue {class_name} size={size} at t={now}: "
            f"{consumed.outcome.value} (tokens_remaining={consumed.tokens_remaining})"
        )
        return EnqueueResult(class_name, consumed.outcome, consumed.tokens_remaining)


def run_contention(
    shaper: ToyShaper, offered: tuple[tuple[str, float], ...]
) -> tuple[EnqueueResult, ...]:
    """Feed every (class_name, size) offer through the shaper in order, in one shared instant.

    With video's bucket drained low and bulk's bucket left untouched, the same clock tick
    (`now` held constant across the whole offered sequence) should throttle video while
    bulk still sails through - proving isolation: video's exhaustion never touches bulk's
    balance, because they are two different TokenBucket objects, not two views onto one.
    """
    results = []
    for class_name, size in offered:
        results.append(shaper.enqueue(class_name, size, shaper.clock))
    return tuple(results)


if __name__ == "__main__":
    from .classes import TrafficClass

    tree = ClassTree(
        classes={
            "default": TrafficClass("default", guaranteed_rate=100, parent=None),
            "video": TrafficClass("video", guaranteed_rate=60, parent="default"),
            "bulk": TrafficClass("bulk", guaranteed_rate=30, parent="default"),
        }
    )
    shaper = ToyShaper(
        tree=tree,
        buckets={
            "video": TokenBucket(capacity=20, tokens=5, rate_per_sec=1, last_refill_at=0),
            "bulk": TokenBucket(capacity=20, tokens=20, rate_per_sec=1, last_refill_at=0),
        },
    )

    # video has only 5 tokens left; bulk sits at full capacity. Same instant, same shaper,
    # two independent buckets: video should throttle, bulk should sail through untouched.
    results = run_contention(
        shaper,
        offered=(
            ("video", 10),
            ("bulk", 10),
        ),
    )
    video_result, bulk_result = results
    assert video_result.outcome is ConsumeOutcome.THROTTLED
    assert bulk_result.outcome is ConsumeOutcome.ALLOWED
    assert bulk_result.tokens_remaining == 10  # bulk's balance, untouched by video's throttle

    # Burst under a token bucket vs. what a leaky bucket would have done to the same burst:
    # video's bucket, refilled since t=0, now has room for its full capacity in one shot.
    shaper.tick(5)  # t=5: video has had 5 seconds at 1/sec to refill - not the full 20
    burst_result = shaper.enqueue("video", 10, shaper.clock)
    assert burst_result.outcome is ConsumeOutcome.ALLOWED  # a token bucket permits this burst

    leaky_twin = LeakyBucket(capacity=20, level=20, leak_per_sec=1, last_leak_at=0)
    leaky_burst = offer(leaky_twin, 10, now=5)
    # The leaky bucket only drained 5 seconds * 1/sec = 5 units of room since it started
    # full, so the same 10-unit burst does not fit - the same burst, two temperaments:
    # the token bucket judges the balance available NOW and lets the whole burst through,
    # the leaky bucket judges only how much has drained and rejects what doesn't fit.
    assert leaky_burst.outcome is OfferOutcome.OVERFLOWED

    for line in shaper.trace:
        print(line)
    print("[OK] shaper_loop.py")
