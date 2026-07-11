from protocol_in_code.qos.token_bucket import ConsumeOutcome, TokenBucket, try_consume


def main() -> None:
    print("Session 01 walkthrough: A token bucket is two variables")
    print()

    bucket = TokenBucket(capacity=10, tokens=10, rate_per_sec=1, last_refill_at=0)

    full_drain = try_consume(bucket, 10, now=0)
    marker = "OK" if full_drain.outcome is ConsumeOutcome.ALLOWED and bucket.tokens == 0 else "NG"
    print(f"[{marker}] drain to zero at t=0        -> {full_drain.outcome.value} tokens={bucket.tokens}")

    short = try_consume(bucket, 1, now=0)
    marker = "OK" if short.outcome is ConsumeOutcome.THROTTLED else "NG"
    print(f"[{marker}] ask again, no time passed   -> {short.outcome.value} tokens={bucket.tokens}")

    self_refilled = try_consume(bucket, 3, now=3)
    marker = "OK" if self_refilled.outcome is ConsumeOutcome.ALLOWED and bucket.tokens == 0 else "NG"
    print(f"[{marker}] 3s later, self-refilled      -> {self_refilled.outcome.value} tokens={bucket.tokens}")

    still_short = try_consume(bucket, 5, now=4)
    marker = "OK" if still_short.outcome is ConsumeOutcome.THROTTLED else "NG"
    print(f"[{marker}] 1s later, not enough yet     -> {still_short.outcome.value} tokens={bucket.tokens}")

    idle_capped = try_consume(bucket, 10, now=1000)
    marker = "OK" if idle_capped.outcome is ConsumeOutcome.ALLOWED and bucket.tokens == 0 else "NG"
    print(f"[{marker}] idle 996s, capped at capacity -> {idle_capped.outcome.value} tokens={bucket.tokens}")

    over_capacity = try_consume(bucket, 11, now=1001)
    marker = "OK" if over_capacity.outcome is ConsumeOutcome.THROTTLED else "NG"
    print(f"[{marker}] ask for more than capacity   -> {over_capacity.outcome.value} tokens={bucket.tokens}")


if __name__ == "__main__":
    main()
