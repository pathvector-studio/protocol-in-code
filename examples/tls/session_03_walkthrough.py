from protocol_in_code.tls.key_schedule import advance_to_handshake, advance_to_master, derive, start_schedule


def main() -> None:
    print("Session 03 walkthrough: Keys grow on a schedule")
    print()

    same_a = derive("secret", "label")
    same_b = derive("secret", "label")
    marker = "OK" if same_a == same_b else "NG"
    print(f"[{marker}] derive is deterministic          -> same inputs, same digest")

    different_label = derive("secret", "other label")
    marker = "OK" if different_label != same_a else "NG"
    print(f"[{marker}] different label changes output   -> digests differ")

    schedule_a = start_schedule(psk="shared-psk")
    advance_to_handshake(schedule_a, shared_key="ecdhe-shared")
    advance_to_master(schedule_a)

    schedule_b = start_schedule(psk="shared-psk")
    advance_to_handshake(schedule_b, shared_key="ecdhe-shared")
    advance_to_master(schedule_b)

    marker = "OK" if schedule_a.master_secret == schedule_b.master_secret else "NG"
    print(f"[{marker}] same psk+shared_key twice        -> identical master secrets")

    schedule_c = start_schedule(psk="different-psk")
    advance_to_handshake(schedule_c, shared_key="ecdhe-shared")
    advance_to_master(schedule_c)

    marker = "OK" if (
        schedule_c.early_secret != schedule_a.early_secret
        and schedule_c.handshake_secret != schedule_a.handshake_secret
        and schedule_c.master_secret != schedule_a.master_secret
    ) else "NG"
    print(f"[{marker}] changing psk changes every downstream secret -> early/handshake/master all differ")

    marker = "OK" if schedule_a.client_hs_traffic != schedule_a.server_hs_traffic else "NG"
    print(f"[{marker}] client_hs_traffic != server_hs_traffic       -> distinct traffic secrets")

    fresh = start_schedule(psk="")
    marker = "OK" if fresh.handshake_secret is None and fresh.master_secret is None else "NG"
    print(f"[{marker}] fresh schedule has no downstream secrets yet -> handshake=None master=None")

    try:
        advance_to_master(fresh)
        marker = "NG"
        note = "no exception raised"
    except ValueError:
        marker = "OK"
        note = "ValueError raised"
    print(f"[{marker}] master secret before handshake secret exists -> {note}")


if __name__ == "__main__":
    main()
