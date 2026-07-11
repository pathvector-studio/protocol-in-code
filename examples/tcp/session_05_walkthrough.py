from protocol_in_code.tcp.rto import MAX_RTO_MS, MIN_RTO_MS, RttEstimator, observe, on_timeout, rto


def main() -> None:
    print("Session 05 walkthrough: The timer learns the network")
    print()

    estimator = RttEstimator()

    cold = rto(estimator)
    marker = "OK" if cold == MIN_RTO_MS else "NG"
    print(f"[{marker}] no samples yet              -> rto={cold}ms")

    observe(estimator, 800)
    seeded = rto(estimator)
    marker = "OK" if estimator.srtt == 800 and estimator.rttvar == 400 and seeded == 2400 else "NG"
    print(f"[{marker}] first sample seeds estimator -> srtt={estimator.srtt} rttvar={estimator.rttvar} rto={seeded}ms")

    for _ in range(5):
        observe(estimator, 800)
    stable = rto(estimator)
    marker = "OK" if stable < seeded else "NG"
    print(f"[{marker}] stable network tightens rto  -> srtt={estimator.srtt:.1f} rttvar={estimator.rttvar:.1f} rto={stable}ms")

    observe(estimator, 3000)
    spiky = rto(estimator)
    marker = "OK" if spiky > stable else "NG"
    print(f"[{marker}] one spiky sample widens rto  -> srtt={estimator.srtt:.1f} rttvar={estimator.rttvar:.1f} rto={spiky}ms")

    doubled = on_timeout(spiky)
    marker = "OK" if doubled == spiky * 2 else "NG"
    print(f"[{marker}] timeout doubles the timer    -> rto {spiky}ms -> {doubled}ms")

    capped = on_timeout(MAX_RTO_MS)
    marker = "OK" if capped == MAX_RTO_MS else "NG"
    print(f"[{marker}] doubling is capped at max     -> rto {MAX_RTO_MS}ms -> {capped}ms")


if __name__ == "__main__":
    main()
