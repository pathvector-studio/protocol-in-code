from protocol_in_code.rip.count_to_infinity import simulate_count_to_infinity, simulate_with_split_horizon
from protocol_in_code.rip.infinity import INFINITY


def main() -> None:
    print("Session 04 walkthrough: Rumors can circle back")
    print()

    naive = simulate_count_to_infinity(max_rounds=20)

    round_1 = naive.rounds[0]
    marker = "OK" if round_1.a_metric == 3 and round_1.b_metric == 4 else "NG"
    print(f"[{marker}] round 1, no split horizon    -> A={round_1.a_metric} B={round_1.b_metric}")

    round_4 = naive.rounds[3]
    marker = "OK" if round_4.a_metric > round_1.a_metric and round_4.b_metric > round_1.b_metric else "NG"
    print(f"[{marker}] round 4 strictly higher       -> A={round_4.a_metric} B={round_4.b_metric}")

    final_round = naive.rounds[-1]
    marker = "OK" if final_round.a_metric == INFINITY and final_round.b_metric == INFINITY else "NG"
    print(f"[{marker}] only stops at INFINITY         -> A={final_round.a_metric} B={final_round.b_metric}")

    marker = "OK" if naive.converged_at == 8 else "NG"
    print(f"[{marker}] eight rounds to count up       -> converged_at={naive.converged_at}")

    marker = "OK" if len(naive.rounds) == naive.converged_at else "NG"
    print(f"[{marker}] rounds tuple matches converged  -> len={len(naive.rounds)}")

    fixed = simulate_with_split_horizon(max_rounds=20)

    marker = "OK" if fixed.converged_at == 1 else "NG"
    print(f"[{marker}] same topology, one filter, eight rounds become one -> converged_at={fixed.converged_at}")

    round_1_fixed = fixed.rounds[0]
    marker = "OK" if round_1_fixed.a_metric == INFINITY and round_1_fixed.b_metric == 2 else "NG"
    print(f"[{marker}] round 1 with split horizon     -> A={round_1_fixed.a_metric} B={round_1_fixed.b_metric}")

    marker = "OK" if len(fixed.rounds) == fixed.converged_at else "NG"
    print(f"[{marker}] rounds tuple matches converged  -> len={len(fixed.rounds)}")


if __name__ == "__main__":
    main()
