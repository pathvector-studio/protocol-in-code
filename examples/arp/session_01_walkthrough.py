from protocol_in_code.arp.cache import NeighborCache, NeighborState, confirm, lookup, start_resolution


def main() -> None:
    print("Session 01 walkthrough: The cache has moods")
    print()

    cache = NeighborCache()

    start_resolution(cache, "10.0.0.2", now=0)
    incomplete = lookup(cache, "10.0.0.2", now=0)
    marker = "OK" if incomplete.state is NeighborState.INCOMPLETE and incomplete.mac is None else "NG"
    print(f"[{marker}] mid-resolution, no reply yet -> {incomplete.state.value} mac={incomplete.mac}")

    confirm(cache, "10.0.0.2", "AA:BB:CC:00:00:02", now=0)
    fresh = lookup(cache, "10.0.0.2", now=0)
    marker = "OK" if fresh.state is NeighborState.REACHABLE and fresh.mac == "AA:BB:CC:00:00:02" else "NG"
    print(f"[{marker}] fresh confirm                -> {fresh.state.value} mac={fresh.mac}")

    one_before = lookup(cache, "10.0.0.2", now=29)
    marker = "OK" if one_before.state is NeighborState.REACHABLE else "NG"
    print(f"[{marker}] one tick before the boundary  -> {one_before.state.value} mac={one_before.mac}")

    at_boundary = lookup(cache, "10.0.0.2", now=30)
    marker = "OK" if at_boundary.state is NeighborState.STALE and at_boundary.mac == "AA:BB:CC:00:00:02" else "NG"
    print(f"[{marker}] at exactly REACHABLE_SECONDS  -> {at_boundary.state.value} mac={at_boundary.mac} (degraded, not gone)")

    still_stale = lookup(cache, "10.0.0.2", now=45)
    marker = "OK" if still_stale.state is NeighborState.STALE and still_stale.mac == "AA:BB:CC:00:00:02" else "NG"
    print(f"[{marker}] well past the boundary        -> {still_stale.state.value} mac={still_stale.mac}")

    start_resolution(cache, "10.0.0.9", now=45)
    unresolved = lookup(cache, "10.0.0.9", now=45)
    marker = "OK" if unresolved.state is NeighborState.INCOMPLETE and unresolved.mac is None else "NG"
    print(f"[{marker}] a second IP, still incomplete -> {unresolved.state.value} mac={unresolved.mac}")

    confirm(cache, "10.0.0.2", "AA:BB:CC:00:00:02", now=50)
    restored = lookup(cache, "10.0.0.2", now=50)
    marker = "OK" if restored.state is NeighborState.REACHABLE and restored.mac == "AA:BB:CC:00:00:02" else "NG"
    print(f"[{marker}] a later confirm restores it   -> {restored.state.value} mac={restored.mac}")

    unknown = lookup(cache, "10.0.0.99", now=50)
    marker = "OK" if unknown.state is None and unknown.mac is None else "NG"
    print(f"[{marker}] an IP never asked about       -> state={unknown.state} mac={unknown.mac}")


if __name__ == "__main__":
    main()
