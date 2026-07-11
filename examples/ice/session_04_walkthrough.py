from protocol_in_code.ice.candidates import Candidate, CandidateType
from protocol_in_code.ice.checklist import (
    Connectivity,
    check_pair,
    form_checklist,
    pair_priority,
    run_checklist,
)


def main() -> None:
    print("Session 04 walkthrough: Pairs are checked in priority order")
    print()

    # pair_priority is symmetric in the min/max sense: swapping which side is
    # "local" and which is "remote" for the SAME pair changes nothing but the
    # tie bit, because the formula sorts by min/max, not by argument position.
    same_direction = pair_priority(126, 100, controlling_is_larger=True)
    swapped_direction = pair_priority(100, 126, controlling_is_larger=True)
    marker = "OK" if same_direction == swapped_direction else "NG"
    print(f"[{marker}] pair_priority(126,100) == pair_priority(100,126) -> {same_direction} == {swapped_direction}")

    tie_bit_off = pair_priority(126, 100, controlling_is_larger=False)
    marker = "OK" if same_direction == tie_bit_off + 1 else "NG"
    print(f"[{marker}] only the tie bit differs                -> {same_direction} vs {tie_bit_off}")

    host = Candidate(ctype=CandidateType.HOST, ip="10.0.0.5", port=5000, base_ip="10.0.0.5", base_port=5000)
    reflexive = Candidate(ctype=CandidateType.SERVER_REFLEXIVE, ip="203.0.113.10", port=40000, base_ip="10.0.0.5", base_port=5000)
    relayed = Candidate(ctype=CandidateType.RELAYED, ip="198.51.100.1", port=7000, base_ip="10.0.0.5", base_port=5000)

    checklist = form_checklist((host, reflexive, relayed), (host, reflexive, relayed))
    marker = "OK" if checklist[0].priority > checklist[-1].priority else "NG"
    print(f"[{marker}] form_checklist sorts descending           -> {checklist[0].priority} > {checklist[-1].priority}")

    # A reality where only the LAST pair in the checklist can succeed: run_checklist
    # still has to walk past every earlier failure, so checked == total pairs.
    late_success = Connectivity(reachable_type_pairs=frozenset({(CandidateType.RELAYED.value, CandidateType.RELAYED.value)}))
    late_result = run_checklist(checklist, late_success)
    marker = "OK" if late_result.nominated is not None and late_result.checked == len(checklist) else "NG"
    print(f"[{marker}] worst-case pair checks every pair          -> checked={late_result.checked}/{len(checklist)}")

    # A reality where the very first (highest-priority) pair succeeds: stop
    # immediately, so checked is far less than the number of pairs formed.
    early_success = Connectivity(reachable_type_pairs=frozenset({(CandidateType.HOST.value, CandidateType.HOST.value)}))
    early_result = run_checklist(checklist, early_success)
    marker = "OK" if early_result.checked < len(checklist) else "NG"
    print(f"[{marker}] first success stops the walk               -> checked={early_result.checked} < total={len(checklist)}")

    # A reality with no reachable combinations at all: every pair is checked
    # and fails, nominated stays None, and checked equals the full checklist.
    no_reality = Connectivity(reachable_type_pairs=frozenset())
    empty_result = run_checklist(checklist, no_reality)
    marker = "OK" if empty_result.nominated is None and empty_result.checked == len(checklist) else "NG"
    print(f"[{marker}] no reachable pairs -> nominated None       -> nominated={empty_result.nominated}, checked={empty_result.checked}/{len(checklist)}")

    # check_pair itself is a direct lookup against the caller-declared ground
    # truth, nothing more - the same pair either is or is not in reachable_type_pairs.
    outcome = check_pair(checklist[0], early_success)
    marker = "OK" if outcome.value == "Succeeded" else "NG"
    print(f"[{marker}] check_pair asks reality, not theory        -> {outcome.value}")


if __name__ == "__main__":
    main()
