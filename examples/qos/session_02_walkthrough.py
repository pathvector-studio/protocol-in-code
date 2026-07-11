from protocol_in_code.qos.refill import compute_refill


def main() -> None:
    print("Session 02 walkthrough: Refill is lazy")
    print()

    exact = compute_refill(tokens=0, capacity=100, rate_per_sec=2, last_refill_at=0, now=5)
    marker = "OK" if exact.tokens == 10 and exact.last_refill_at == 5 else "NG"
    print(f"[{marker}] elapsed(5) * rate(2)         -> tokens={exact.tokens} last_refill_at={exact.last_refill_at}")

    zero_elapsed = compute_refill(tokens=10, capacity=100, rate_per_sec=2, last_refill_at=5, now=5)
    marker = "OK" if zero_elapsed.tokens == 10 and zero_elapsed.last_refill_at == 5 else "NG"
    print(f"[{marker}] zero elapsed adds nothing    -> tokens={zero_elapsed.tokens} last_refill_at={zero_elapsed.last_refill_at}")

    negative_elapsed = compute_refill(tokens=10, capacity=100, rate_per_sec=2, last_refill_at=8, now=5)
    marker = "OK" if negative_elapsed.tokens == 10 and negative_elapsed.last_refill_at == 8 else "NG"
    print(f"[{marker}] now before last_refill_at    -> tokens={negative_elapsed.tokens} last_refill_at={negative_elapsed.last_refill_at}")

    capped = compute_refill(tokens=0, capacity=100, rate_per_sec=2, last_refill_at=0, now=500)
    marker = "OK" if capped.tokens == 100 and capped.last_refill_at == 500 else "NG"
    print(f"[{marker}] long idle capped at capacity -> tokens={capped.tokens} last_refill_at={capped.last_refill_at}")

    from_partial = compute_refill(tokens=40, capacity=100, rate_per_sec=2, last_refill_at=0, now=500)
    marker = "OK" if from_partial.tokens == 100 and from_partial.last_refill_at == 500 else "NG"
    print(f"[{marker}] partial balance also capped  -> tokens={from_partial.tokens} last_refill_at={from_partial.last_refill_at}")

    scalars_only = compute_refill(tokens=0, capacity=5, rate_per_sec=1, last_refill_at=0, now=1)
    marker = "OK" if scalars_only.tokens == 1 and scalars_only.last_refill_at == 1 else "NG"
    print(f"[{marker}] plain scalars in, scalars out -> tokens={scalars_only.tokens} last_refill_at={scalars_only.last_refill_at}")


if __name__ == "__main__":
    main()
