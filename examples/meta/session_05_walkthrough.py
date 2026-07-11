from protocol_in_code.meta.the_loop import (
    LoopSummary,
    common_skeleton,
    run_two_loops_side_by_side,
    survey,
)


def main() -> None:
    print("Session 05 walkthrough: Every protocol ends in a loop")
    print()

    rows = survey()
    marker = "OK" if len(rows) == 22 else "NG"
    print(f"[{marker}] survey() returns 22 rows                 -> {len(rows)}")

    all_traced = all(row.decision_trace is True for row in rows)
    marker = "OK" if all_traced else "NG"
    print(f"[{marker}] every LoopSummary.decision_trace is True -> {all_traced}")

    marker = "OK" if isinstance(rows[0], LoopSummary) else "NG"
    print(f"[{marker}] rows are LoopSummary instances            -> {type(rows[0]).__name__}")

    skeleton = common_skeleton()
    marker = "OK" if len(skeleton) == 6 else "NG"
    print(f"[{marker}] common_skeleton() has 6 steps             -> {len(skeleton)}")

    dns_line, tcp_line = run_two_loops_side_by_side()
    marker = "OK" if bool(dns_line) and bool(tcp_line) else "NG"
    print(f"[{marker}] both trace lines non-empty                -> dns={dns_line!r} tcp={tcp_line!r}")

    marker = "OK" if dns_line != tcp_line else "NG"
    print(f"[{marker}] the two trace lines differ                -> {dns_line != tcp_line}")

    print(f"[OK] the course taught 22 protocols; it also taught one program, twenty-two times.")


if __name__ == "__main__":
    main()
