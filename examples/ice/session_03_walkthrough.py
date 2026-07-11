from protocol_in_code.ice.candidates import CandidateType, TYPE_PREFERENCE, candidate_priority, gather
from protocol_in_code.ice.stun import BindingResponse


def main() -> None:
    print("Session 03 walkthrough: candidates are gathered, not chosen")
    print()

    local_addr = ("10.0.0.5", 55555)

    host_only = gather(local_addr, stun_response=None, turn_addr=None)
    marker = "OK" if len(host_only) == 1 and host_only[0].ctype is CandidateType.HOST else "NG"
    print(f"[{marker}] no STUN, no TURN -> host only          -> {[c.ctype.value for c in host_only]}")

    differing_stun = BindingResponse(mapped_ip="203.0.113.9", mapped_port=62000)
    with_reflexive = gather(local_addr, stun_response=differing_stun, turn_addr=None)
    marker = "OK" if [c.ctype for c in with_reflexive] == [CandidateType.HOST, CandidateType.SERVER_REFLEXIVE] else "NG"
    print(f"[{marker}] STUN response differs -> +reflexive     -> {[c.ctype.value for c in with_reflexive]}")

    same_as_local = BindingResponse(mapped_ip=local_addr[0], mapped_port=local_addr[1])
    no_reflexive = gather(local_addr, stun_response=same_as_local, turn_addr=None)
    marker = "OK" if [c.ctype for c in no_reflexive] == [CandidateType.HOST] else "NG"
    print(f"[{marker}] STUN response same as local -> NO reflexive -> {[c.ctype.value for c in no_reflexive]}")

    turn_addr = ("198.51.100.7", 3478)
    with_relayed = gather(local_addr, stun_response=None, turn_addr=turn_addr)
    marker = "OK" if [c.ctype for c in with_relayed] == [CandidateType.HOST, CandidateType.RELAYED] else "NG"
    print(f"[{marker}] TURN allocation given -> +relayed       -> {[c.ctype.value for c in with_relayed]}")

    everything = gather(local_addr, stun_response=differing_stun, turn_addr=turn_addr)
    marker = "OK" if [c.ctype for c in everything] == [
        CandidateType.HOST,
        CandidateType.SERVER_REFLEXIVE,
        CandidateType.RELAYED,
    ] else "NG"
    print(f"[{marker}] STUN differs + TURN given -> all three   -> {[c.ctype.value for c in everything]}")

    host_prio = candidate_priority(CandidateType.HOST, local_pref=65535)
    reflexive_prio = candidate_priority(CandidateType.SERVER_REFLEXIVE, local_pref=65535)
    relayed_prio = candidate_priority(CandidateType.RELAYED, local_pref=65535)
    marker = "OK" if host_prio > reflexive_prio > relayed_prio else "NG"
    print(f"[{marker}] priority HOST({host_prio}) > REFLEXIVE({reflexive_prio}) > RELAYED({relayed_prio})")

    marker = "OK" if (TYPE_PREFERENCE[CandidateType.HOST], TYPE_PREFERENCE[CandidateType.SERVER_REFLEXIVE], TYPE_PREFERENCE[CandidateType.RELAYED]) == (126, 100, 0) else "NG"
    print(f"[{marker}] type preferences are 126 / 100 / 0, RFC 8445 SS5.1.2.2 defaults")


if __name__ == "__main__":
    main()
