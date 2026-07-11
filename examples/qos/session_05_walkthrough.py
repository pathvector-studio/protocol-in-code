from protocol_in_code.qos.classes import ClassTree, TrafficClass
from protocol_in_code.qos.shaper_loop import ToyShaper, run_contention
from protocol_in_code.qos.token_bucket import ConsumeOutcome, TokenBucket


def main() -> None:
    print("Session 05 walkthrough: Build the toy shaper loop")
    print()

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

    # Same instant, same shaper, two independent buckets: video is nearly drained
    # (5 tokens), bulk sits at full capacity (20 tokens). Isolation means video's
    # exhaustion cannot borrow from or bleed into bulk's balance.
    video_result, bulk_result = run_contention(
        shaper, offered=(("video", 10), ("bulk", 10))
    )
    marker = "OK" if video_result.outcome is ConsumeOutcome.THROTTLED else "NG"
    print(f"[{marker}] video: 5 tokens, asks 10 at t=0 -> {video_result.outcome.value}")

    marker = "OK" if bulk_result.outcome is ConsumeOutcome.ALLOWED and bulk_result.tokens_remaining == 10 else "NG"
    print(f"[{marker}] bulk: 20 tokens, asks 10 at t=0 -> {bulk_result.outcome.value} tokens_remaining={bulk_result.tokens_remaining}")

    # Time passing refills video's own bucket independently of bulk. 5 seconds at
    # 1/sec adds 5 tokens to the same balance that was just throttled.
    shaper.tick(5)
    video_retry = shaper.enqueue("video", 5, shaper.clock)
    marker = "OK" if video_retry.outcome is ConsumeOutcome.ALLOWED else "NG"
    print(f"[{marker}] video: 5s later, retry for 5    -> {video_retry.outcome.value} tokens_remaining={video_retry.tokens_remaining}")

    # enqueue() looks the class up with a plain dict index (self.buckets[class_name]);
    # there is no branch for a missing class, so an unknown name raises KeyError
    # straight out of the dict lookup rather than returning a THROTTLED result.
    try:
        shaper.enqueue("unknown_class", 1, shaper.clock)
        marker = "NG"
        detail = "no exception raised"
    except KeyError:
        marker = "OK"
        detail = "KeyError"
    print(f"[{marker}] unknown class name              -> raises {detail}")

    # The shaper's trace is the source of truth for everything that happened above,
    # including the throttle line for video's first request.
    has_throttle_line = any("video size=10 at t=0: Throttled" in line for line in shaper.trace)
    marker = "OK" if len(shaper.trace) > 0 and has_throttle_line else "NG"
    print(f"[{marker}] trace non-empty, throttle logged -> {len(shaper.trace)} lines")

    print()
    for line in shaper.trace:
        print(line)


if __name__ == "__main__":
    main()
