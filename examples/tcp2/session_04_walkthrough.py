from protocol_in_code.tcp2.keepalive import (
    KEEPALIVE_COUNT,
    KEEPALIVE_IDLE,
    KEEPALIVE_INTERVAL,
    KeepaliveVerdict,
    connection_verdict,
    probe_times,
)


def main() -> None:
    print("Session 04 walkthrough: Keepalive probes an idle line")
    print()

    last_activity = 1_000
    times = probe_times(last_activity)

    marker = "OK" if len(times) == KEEPALIVE_COUNT else "NG"
    print(f"[{marker}] nine probes scheduled     -> {len(times)} entries")

    marker = "OK" if times[0] == last_activity + KEEPALIVE_IDLE else "NG"
    print(f"[{marker}] first probe at last+7200  -> {times[0]}")

    spaced_75 = all(times[i + 1] - times[i] == KEEPALIVE_INTERVAL for i in range(len(times) - 1))
    marker = "OK" if spaced_75 else "NG"
    print(f"[{marker}] each later probe +75s     -> {times}")

    still_idle = connection_verdict(last_activity, (), last_activity + KEEPALIVE_IDLE - 1)
    marker = "OK" if still_idle is KeepaliveVerdict.ALIVE else "NG"
    print(f"[{marker}] one tick before idle ends -> {still_idle.value}")

    mid_sequence = connection_verdict(last_activity, (False, False, False), times[2])
    marker = "OK" if mid_sequence is KeepaliveVerdict.PROBING else "NG"
    print(f"[{marker}] mid-sequence, 3 unanswered -> {mid_sequence.value}")

    all_nine_silent = tuple([False] * KEEPALIVE_COUNT)
    boundary = connection_verdict(last_activity, all_nine_silent, times[KEEPALIVE_COUNT - 1])
    marker = "OK" if boundary is KeepaliveVerdict.DEAD else "NG"
    print(f"[{marker}] exactly the 9th probe time -> {boundary.value}")

    one_tick_earlier = connection_verdict(last_activity, all_nine_silent[:8], times[KEEPALIVE_COUNT - 1] - 1)
    marker = "OK" if one_tick_earlier is KeepaliveVerdict.PROBING else "NG"
    print(f"[{marker}] one tick before that       -> {one_tick_earlier.value}")

    one_answered = (False, False, False, False, True, False, False, False, False)
    revived = connection_verdict(last_activity, one_answered, times[KEEPALIVE_COUNT - 1])
    marker = "OK" if revived is KeepaliveVerdict.ALIVE else "NG"
    print(f"[{marker}] one answered probe revives -> {revived.value}")

    udp_mapping_timeout = 30
    nat_mismatch = KEEPALIVE_IDLE > udp_mapping_timeout * 100
    marker = "OK" if nat_mismatch else "NG"
    print(f"[{marker}] NAT mismatch: 30s vs 7200s -> UDP mapping dies long before the first probe is due")


if __name__ == "__main__":
    main()
