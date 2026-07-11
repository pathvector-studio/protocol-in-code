from protocol_in_code.nat.ports import EPHEMERAL_RANGE, AllocationOutcome, PortAllocator, allocate_port, release_port


def main() -> None:
    print("Session 04 walkthrough: Ports are a shared resource")
    print()

    alloc = PortAllocator(public_ip="203.0.113.9")

    first = allocate_port(alloc)
    marker = "OK" if first == EPHEMERAL_RANGE[0] else "NG"
    print(f"[{marker}] first allocation starts low  -> {first}")

    second = allocate_port(alloc)
    third = allocate_port(alloc)
    marker = "OK" if second == first + 1 and third == first + 2 else "NG"
    print(f"[{marker}] sequential allocations       -> {first}, {second}, {third}")

    release_port(alloc, second)
    reused = second not in alloc.in_use
    marker = "OK" if reused else "NG"
    print(f"[{marker}] release_port frees the port  -> {second} back in pool")

    fourth = allocate_port(alloc)
    marker = "OK" if fourth == first + 3 else "NG"
    print(f"[{marker}] scan resumes past next_candidate, not the freed gap -> {fourth}")

    low, high = EPHEMERAL_RANGE
    span = high - low + 1

    tiny_alloc = PortAllocator(public_ip="203.0.113.9", in_use=set(range(low, high)), next_candidate=low)
    almost_full = allocate_port(tiny_alloc)
    marker = "OK" if almost_full == high else "NG"
    print(f"[{marker}] one port left in the pool    -> {almost_full}")

    full_alloc = PortAllocator(public_ip="203.0.113.9", in_use=set(range(low, high + 1)), next_candidate=low)
    exhausted = allocate_port(full_alloc)
    marker = "OK" if exhausted is None else "NG"
    print(f"[{marker}] every port in_use            -> {exhausted} ({AllocationOutcome.POOL_EXHAUSTED.value})")

    wrap_alloc = PortAllocator(
        public_ip="203.0.113.9",
        in_use=set(range(low, high + 1)) - {low, high - 1},
        next_candidate=high - 5,
    )
    wrapped = allocate_port(wrap_alloc)
    marker = "OK" if wrapped == high - 1 else "NG"
    print(f"[{marker}] scan finds a gap before wrap  -> {wrapped}")

    wrapped_again = allocate_port(wrap_alloc)
    marker = "OK" if wrapped_again == low else "NG"
    print(f"[{marker}] scan wraps past the top of the range -> {wrapped_again}")


if __name__ == "__main__":
    main()
