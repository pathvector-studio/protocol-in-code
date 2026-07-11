from protocol_in_code.stp.root_election import BridgeId
from protocol_in_code.stp.stp_loop import converge, fail_root, triangle


def main() -> None:
    print("Session 05 walkthrough: Build the toy spanning tree loop")
    print()

    bridges, segments = triangle()
    report = converge(bridges, segments, rounds=10)

    marker = "OK" if report.rounds_run == 2 else "NG"
    print(f"[{marker}] triangle converges in 2 rounds        -> rounds_run={report.rounds_run}")

    expected_root = BridgeId(priority=4096, mac="00:00:00:00:00:0a")
    marker = "OK" if report.root == expected_root else "NG"
    print(f"[{marker}] unanimous root is A's BridgeId          -> root={report.root.mac}")

    marker = "OK" if len(report.blocked_ports) == 1 else "NG"
    print(f"[{marker}] exactly one port blocked                -> blocked_ports={report.blocked_ports}")

    marker = "OK" if report.blocked_ports == (("C", 2),) else "NG"
    print(f"[{marker}] the blocked port is C's port 2           -> blocked_ports={report.blocked_ports}")

    # C's trace records the BPDU that made port 2 the losing side of the
    # blocking.py collision: A's own claim, heard directly, cost 19.
    expected_trace_line = "00:00:00:00:00:0c: port 2 now hears root=00:00:00:00:00:0a cost=19"
    marker = "OK" if expected_trace_line in bridges["C"].trace else "NG"
    print(f"[{marker}] C's trace records hearing A's BPDU on port 2 -> {expected_trace_line!r} in trace")

    # --- fail_root: take A down and re-converge ---
    bridges2, segments2 = triangle()
    converge(bridges2, segments2, rounds=10)
    failure_report = fail_root(bridges2, segments2, failed_name="A", rounds=10)

    expected_new_root = BridgeId(priority=32768, mac="00:00:00:00:00:0b")
    marker = "OK" if failure_report.root == expected_new_root else "NG"
    print(f"[{marker}] new root after A fails is B              -> root={failure_report.root.mac}")

    # Removing the root removed the loop itself - with only B and C left,
    # there is exactly one segment (seg-bc) between them, so there is
    # nothing left to block. The spare tire scenario does not apply here:
    # what "unblocks" is not a port coming into service, it's the loop
    # ceasing to exist.
    marker = "OK" if failure_report.blocked_ports == () else "NG"
    print(f"[{marker}] blocked is empty: removing the root removed the loop -> blocked_ports={failure_report.blocked_ports}")


if __name__ == "__main__":
    main()
