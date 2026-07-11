from protocol_in_code.ice.candidates import CandidateType
from protocol_in_code.ice.ice_loop import scenario_direct_fails, scenario_hard_nats


def main() -> None:
    print("Session 05 walkthrough: Build the toy connectivity check loop")
    print()

    direct = scenario_direct_fails()
    marker = "OK" if direct.nominated_pair is not None else "NG"
    print(f"[{marker}] direct-fails: a pair got nominated        -> {direct.nominated_pair.local.ctype.value}x{direct.nominated_pair.remote.ctype.value}")

    marker = "OK" if CandidateType.SERVER_REFLEXIVE in (direct.nominated_pair.local.ctype, direct.nominated_pair.remote.ctype) else "NG"
    print(f"[{marker}] direct-fails: nomination involves reflexive -> {direct.nominated_pair.local.ctype.value}x{direct.nominated_pair.remote.ctype.value}")

    direct_check_lines = [line for line in direct.trace if line.startswith("check ")]
    marker = "OK" if direct_check_lines and direct_check_lines[0] == "check 1: HostxHost -> FAILED" else "NG"
    print(f"[{marker}] direct-fails: HostxHost fails first        -> {direct_check_lines[0]}")

    gather_lines = [line for line in direct.trace if "gathered" in line]
    marker = "OK" if len(gather_lines) == 2 else "NG"
    print(f"[{marker}] direct-fails: both agents' gather traced   -> {len(gather_lines)} gather lines")

    marker = "OK" if len(direct.trace) > 0 else "NG"
    print(f"[{marker}] direct-fails: trace is non-empty           -> {len(direct.trace)} lines")

    print()

    hard = scenario_hard_nats()
    marker = "OK" if hard.nominated_pair is not None else "NG"
    print(f"[{marker}] hard-nats: a pair got nominated            -> {hard.nominated_pair.local.ctype.value}x{hard.nominated_pair.remote.ctype.value}")

    marker = "OK" if CandidateType.RELAYED in (hard.nominated_pair.local.ctype, hard.nominated_pair.remote.ctype) else "NG"
    print(f"[{marker}] hard-nats: nomination involves a relay     -> {hard.nominated_pair.local.ctype.value}x{hard.nominated_pair.remote.ctype.value}")

    hard_check_lines = [line for line in hard.trace if line.startswith("check ")]
    failed_before_success = [line for line in hard_check_lines if line.endswith("FAILED")]
    marker = "OK" if len(failed_before_success) == 4 else "NG"
    print(f"[{marker}] hard-nats: exactly 4 failures before success -> {len(failed_before_success)} failures")

    checklist_order_line = next(line for line in hard.trace if line.startswith("checklist formed"))
    marker = "OK" if "HostxHost" in checklist_order_line and checklist_order_line.split(": ")[-1].startswith("HostxHost") else "NG"
    print(f"[{marker}] hard-nats: checklist order lists HostxHost first -> {checklist_order_line}")

    gather_lines_hard = [line for line in hard.trace if "gathered" in line]
    marker = "OK" if len(gather_lines_hard) == 2 and len(hard.trace) > 0 else "NG"
    print(f"[{marker}] hard-nats: trace non-empty, gather lines present -> {len(gather_lines_hard)} gather lines, {len(hard.trace)} total")

    # The headline: ICE is brute force with a priority order. It never
    # understood either NAT - it just tried every candidate pair in the order
    # the priority formula fixed, and the relay was the only pair reality allowed.
    print()
    print("Headline: ICE doesn't understand the NATs, it tries everything both sides could be.")


if __name__ == "__main__":
    main()
