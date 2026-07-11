from protocol_in_code.ha.bfd import BfdSession, BfdState, check_timeout, detection_time, on_packet


def main() -> None:
    print("Session 03 walkthrough: Three states, both directions")
    print()

    # --- The 3-way walk: DOWN + remote DOWN -> INIT ---
    session = BfdSession(
        local_state=BfdState.DOWN,
        remote_state_last_heard=BfdState.DOWN,
        detect_multiplier=3,
        interval_ms=50,
        last_packet_at=0,
    )
    state_after_down_down = on_packet(session, remote_state=BfdState.DOWN, now=10)
    marker = "OK" if state_after_down_down is BfdState.INIT else "NG"
    print(f"[{marker}] DOWN + remote DOWN  -> {state_after_down_down.value} (start negotiating)")

    # --- INIT + remote INIT -> UP ---
    state_after_init_init = on_packet(session, remote_state=BfdState.INIT, now=60)
    marker = "OK" if state_after_init_init is BfdState.UP else "NG"
    print(f"[{marker}] INIT + remote INIT  -> {state_after_init_init.value} (both sides agree)")

    # --- Once UP, hearing INIT or DOWN from the remote does not un-agree the session ---
    # (the "anything else -> unchanged" branch: remote hasn't caught up, local holds its ground)
    state_stays_up = on_packet(session, remote_state=BfdState.INIT, now=110)
    marker = "OK" if state_stays_up is BfdState.UP else "NG"
    print(f"[{marker}] UP + remote INIT     -> {state_stays_up.value} (unchanged branch)")

    # --- The other DOWN entrypoint: DOWN + remote INIT -> UP directly, no INIT stopover ---
    fresh = BfdSession(
        local_state=BfdState.DOWN,
        remote_state_last_heard=BfdState.DOWN,
        detect_multiplier=3,
        interval_ms=50,
        last_packet_at=0,
    )
    state_down_init = on_packet(fresh, remote_state=BfdState.INIT, now=5)
    marker = "OK" if state_down_init is BfdState.UP else "NG"
    print(f"[{marker}] DOWN + remote INIT   -> {state_down_init.value} (peer already trying, agree)")

    # --- detection_time = multiplier * interval, asserted with numbers ---
    expected_detection_time = 3 * 50
    actual_detection_time = detection_time(session)
    marker = "OK" if actual_detection_time == expected_detection_time == 150 else "NG"
    print(f"[{marker}] detection_time = 3 * 50ms          -> {actual_detection_time}ms")

    # --- One ms before detection_time: still UP ---
    session.last_packet_at = 0
    one_ms_before = check_timeout(session, now=149)
    marker = "OK" if one_ms_before is BfdState.UP else "NG"
    print(f"[{marker}] one ms before {actual_detection_time}ms  -> {one_ms_before.value}")

    # --- Exactly at detection_time: drops straight to DOWN, no INIT stopover ---
    exactly_at = check_timeout(session, now=150)
    marker = "OK" if exactly_at is BfdState.DOWN else "NG"
    print(f"[{marker}] exactly at {actual_detection_time}ms     -> {exactly_at.value} (immediate, total)")


if __name__ == "__main__":
    main()
