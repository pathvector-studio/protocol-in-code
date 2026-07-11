from protocol_in_code.qos.leaky_bucket import LeakyBucket, OfferOutcome, offer
from protocol_in_code.qos.token_bucket import ConsumeOutcome, TokenBucket, try_consume


def main() -> None:
    print("Session 03 walkthrough: Leaky and token are cousins")
    print()

    bucket = LeakyBucket(capacity=10, level=0, leak_per_sec=1, last_leak_at=0)

    fill = offer(bucket, 6, now=0)
    marker = "OK" if fill.outcome is OfferOutcome.ACCEPTED and bucket.level == 6 else "NG"
    print(f"[{marker}] arrival fills the level       -> {fill.outcome.value} level={bucket.level}")

    overflow = offer(bucket, 6, now=0)
    marker = "OK" if overflow.outcome is OfferOutcome.OVERFLOWED and bucket.level == 6 else "NG"
    print(f"[{marker}] too much, no time to drain    -> {overflow.outcome.value} level={bucket.level}")

    drained = offer(bucket, 3, now=3)
    marker = "OK" if drained.outcome is OfferOutcome.ACCEPTED and bucket.level == 6 else "NG"
    print(f"[{marker}] 3s later, room opened by leak -> {drained.outcome.value} level={bucket.level}")

    floor_at_zero = offer(bucket, 1, now=1000)
    marker = "OK" if floor_at_zero.outcome is OfferOutcome.ACCEPTED and bucket.level == 1 else "NG"
    print(f"[{marker}] idle so long level floors at 0 -> {floor_at_zero.outcome.value} level={bucket.level}")

    # THE side-by-side: identical capacity, identical burst size, identical timing.
    # A token bucket starts full and permits the whole burst at once. A leaky bucket
    # starts full (level == capacity, nothing has drained yet) and rejects the same
    # burst outright — that is the opposite temperament from the same two variables.
    token_twin = TokenBucket(capacity=10, tokens=10, rate_per_sec=1, last_refill_at=0)
    leaky_twin = LeakyBucket(capacity=10, level=10, leak_per_sec=1, last_leak_at=0)

    token_burst = try_consume(token_twin, 10, now=0)
    leaky_burst = offer(leaky_twin, 10, now=0)
    marker = "OK" if token_burst.outcome is ConsumeOutcome.ALLOWED and leaky_burst.outcome is OfferOutcome.OVERFLOWED else "NG"
    print(f"[{marker}] SAME burst: token ALLOWED, leaky OVERFLOWED -> token={token_burst.outcome.value} leaky={leaky_burst.outcome.value}")


if __name__ == "__main__":
    main()
