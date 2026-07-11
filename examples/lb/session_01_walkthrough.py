from protocol_in_code.lb.round_robin import RoundRobinState, pick, pick_weighted


def main() -> None:
    print("Session 01 walkthrough: Round robin is one index")
    print()

    state = RoundRobinState(backends=("s1", "s2", "s3"))

    first = pick(state)
    marker = "OK" if first == "s1" else "NG"
    print(f"[{marker}] pick 1                    -> {first}")

    second = pick(state)
    marker = "OK" if second == "s2" else "NG"
    print(f"[{marker}] pick 2                    -> {second}")

    third = pick(state)
    marker = "OK" if third == "s3" else "NG"
    print(f"[{marker}] pick 3                    -> {third}")

    fourth = pick(state)
    marker = "OK" if fourth == "s1" else "NG"
    print(f"[{marker}] pick 4 wraps to s1        -> {fourth}")

    weighted_state = RoundRobinState(backends=("s1", "s2"))
    weights = {"s1": 2, "s2": 1}
    cycle = [pick_weighted(weighted_state, weights) for _ in range(3)]
    marker = "OK" if cycle.count("s1") == 2 and cycle.count("s2") == 1 else "NG"
    print(f"[{marker}] weighted 2:1 over 3 picks  -> {cycle}")

    next_cycle = [pick_weighted(weighted_state, weights) for _ in range(3)]
    marker = "OK" if next_cycle == cycle else "NG"
    print(f"[{marker}] next cycle repeats exactly -> {next_cycle}")


if __name__ == "__main__":
    main()
