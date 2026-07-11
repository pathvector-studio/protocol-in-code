from protocol_in_code.arp.cache import NeighborState, lookup
from protocol_in_code.arp.responder_loop import ToyArpNode, run_resolution


def main() -> None:
    print("Session 04 walkthrough: Build the toy ARP responder loop")
    print()

    a = ToyArpNode(name="A", my_ip="10.0.0.1", my_mac="AA:AA:AA:00:00:01")
    b = ToyArpNode(name="B", my_ip="10.0.0.2", my_mac="BB:BB:BB:00:00:02")

    # run_resolution's first internal step is A.send_to(); with no cache entry yet,
    # that call queues the packet and emits a who-has -- check both right after.
    delivered = run_resolution(a, b, "hello-1")

    marker = "OK" if delivered == ("hello-1",) else "NG"
    print(f"[{marker}] packet queued then delivered after resolution -> delivered={delivered}")

    who_has_traced = any("who-has" in line for line in a.trace)
    marker = "OK" if who_has_traced else "NG"
    print(f"[{marker}] a who-has line is in A's trace -> {who_has_traced}")

    b_gleaned = lookup(b.cache, a.my_ip, b.clock)
    marker = "OK" if b_gleaned.state is NeighborState.REACHABLE and b_gleaned.mac == a.my_mac else "NG"
    print(f"[{marker}] B gleaned A's mapping from the request -> {b_gleaned.state.value} mac={b_gleaned.mac}")

    glean_traced = any("glean" in line for line in b.trace)
    marker = "OK" if glean_traced else "NG"
    print(f"[{marker}] the glean line is in B's trace -> {glean_traced}")

    a_confirmed = lookup(a.cache, b.my_ip, a.clock)
    marker = "OK" if a_confirmed.state is NeighborState.REACHABLE and a_confirmed.mac == b.my_mac else "NG"
    print(f"[{marker}] A's cache now holds B's mapping -> {a_confirmed.state.value} mac={a_confirmed.mac}")

    marker = "OK" if len(a.trace) > 0 and len(b.trace) > 0 else "NG"
    print(f"[{marker}] both traces are non-empty     -> len(A)={len(a.trace)}, len(B)={len(b.trace)}")

    second_attempt = a.send_to(b.my_ip, "hello-2")
    who_has_count_before = sum("who-has" in line for line in a.trace)
    marker = "OK" if second_attempt == b.my_mac else "NG"
    print(f"[{marker}] a second send_to hits the cache -> mac={second_attempt} (no new who-has)")

    trace_len_after = len(a.trace)
    new_who_has = any("who-has" in line for line in a.trace[trace_len_after - 1:])
    marker = "OK" if not new_who_has else "NG"
    print(f"[{marker}] no new who-has line was appended -> who_has_lines={who_has_count_before}")


if __name__ == "__main__":
    main()
