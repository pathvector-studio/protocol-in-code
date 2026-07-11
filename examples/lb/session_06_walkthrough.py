from protocol_in_code.lb.lb_loop import Strategy, ToyLoadBalancer


def main() -> None:
    print("Session 06 walkthrough: Build the toy load balancer loop")
    print()

    # --- ROUND_ROBIN skips a DOWN backend ---
    rr = ToyLoadBalancer(backends=("s1", "s2", "s3"), strategy=Strategy.ROUND_ROBIN)
    rr.probe_result("s2", ok=False)
    rr.probe_result("s2", ok=False)
    rr.probe_result("s2", ok=False)
    picks = tuple(rr.route(f"k{i}") for i in range(4))
    marker = "OK" if "s2" not in picks else "NG"
    print(f"[{marker}] RR skips DOWN backend s2       -> {picks}")

    # --- RING affinity holds, then moves only after DOWN ---
    ring_lb = ToyLoadBalancer(backends=("s1", "s2", "s3"), strategy=Strategy.RING)
    streak = tuple(ring_lb.route("sticky-user") for _ in range(4))
    marker = "OK" if len(set(streak)) == 1 else "NG"
    print(f"[{marker}] RING affinity: 4 routes, 1 backend -> {streak}")

    sticky_backend = streak[0]
    ring_lb.probe_result(sticky_backend, ok=False)
    ring_lb.probe_result(sticky_backend, ok=False)
    ring_lb.probe_result(sticky_backend, ok=False)
    moved_to = ring_lb.route("sticky-user")
    marker = "OK" if moved_to != sticky_backend else "NG"
    print(f"[{marker}] RING moves only after {sticky_backend} is DOWN -> now on {moved_to}")

    # --- LEAST_CONN reacts to open/close ---
    lc = ToyLoadBalancer(backends=("a", "b"), strategy=Strategy.LEAST_CONN)
    first = lc.route("x")
    lc.connection_opened(first)
    second = lc.route("y")
    marker = "OK" if second != first else "NG"
    print(f"[{marker}] LEAST_CONN routes around open conn -> {first} then {second}")

    lc.connection_closed(first)
    third = lc.route("z")
    marker = "OK" if third == first else "NG"
    print(f"[{marker}] LEAST_CONN returns to {first} after close -> {third}")

    # --- all backends DOWN -> None ---
    lonely = ToyLoadBalancer(backends=("only1",), strategy=Strategy.ROUND_ROBIN)
    lonely.probe_result("only1", ok=False)
    lonely.probe_result("only1", ok=False)
    lonely.probe_result("only1", ok=False)
    result = lonely.route("anykey")
    marker = "OK" if result is None else "NG"
    print(f"[{marker}] all backends DOWN -> route() returns None -> {result}")

    # --- trace is non-empty and contains a probe line ---
    marker = "OK" if lonely.trace and any(line.startswith("probe only1") for line in lonely.trace) else "NG"
    print(f"[{marker}] trace records the probe that took it down -> {lonely.trace[0]!r}")


if __name__ == "__main__":
    main()
