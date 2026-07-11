from protocol_in_code.igmp.querier import MEMBERSHIP_TIMEOUT
from protocol_in_code.igmp.querier_loop import ToyQuerier, ToySnoopingSwitch, run_query_cycle


def main() -> None:
    print("Session 04 walkthrough: Build the toy querier loop")
    print()

    querier = ToyQuerier()
    switch = ToySnoopingSwitch()

    # host-a and host-b share 224.0.1.5 behind ports 1 and 3 (suppression applies);
    # host-c is alone on 224.0.2.9 behind port 3 and goes silent on the second cycle.
    hosts = {
        "host-a": (1, "224.0.1.5"),
        "host-b": (3, "224.0.1.5"),
        "host-c": (3, "224.0.2.9"),
    }
    silent_hosts = ("host-c",)

    run_query_cycle(querier, switch, hosts, silent_hosts)

    for line in querier.trace:
        print(f"    {line}")
    for line in switch.trace:
        print(f"    {line}")
    print()

    suppression_line = next((line for line in querier.trace if "suppression ->" in line), None)
    marker = "OK" if suppression_line is not None and "1 message(s) saved" in suppression_line else "NG"
    print(f"[{marker}] suppression saved 1 message for the 2-member group -> {suppression_line}")

    expiry_line = next((line for line in querier.trace if "host-c" in line and "expired from" in line), None)
    marker = "OK" if expiry_line is not None and "clock advanced to 260" in "\n".join(querier.trace) else "NG"
    print(f"[{marker}] host-c expired at clock={MEMBERSHIP_TIMEOUT} -> {expiry_line}")

    before_line = next((line for line in querier.trace if "BEFORE expiry" in line), None)
    after_line = next((line for line in querier.trace if "AFTER expiry" in line), None)
    marker = "OK" if before_line is not None and "ports=(0, 3)" in before_line else "NG"
    print(f"[{marker}] forwarding set BEFORE expiry -> {before_line}")
    marker = "OK" if after_line is not None and "ports=(0,)" in after_line else "NG"
    print(f"[{marker}] forwarding set AFTER expiry  -> {after_line}")

    shrink_line = next((line for line in querier.trace if "shrank" in line), None)
    marker = "OK" if shrink_line is not None else "NG"
    print(f"[{marker}] trace names the shrink        -> {shrink_line}")

    prune_line = next((line for line in switch.trace if "pruned" in line), None)
    marker = "OK" if prune_line is not None and "port 3 pruned from 224.0.2.9" in prune_line else "NG"
    print(f"[{marker}] switch prune line             -> {prune_line}")


if __name__ == "__main__":
    main()
