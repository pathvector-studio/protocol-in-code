from protocol_in_code.ha.vrrp_timeout import (
    ADVERTISEMENT_INTERVAL,
    BackupWatch,
    heartbeat,
    master_down_interval,
    master_is_down,
)


def main() -> None:
    print("Session 02 walkthrough: Silence means failure")
    print()

    # --- The skew: a higher-priority backup declares the master dead sooner ---
    high_priority_interval = master_down_interval(254)
    low_priority_interval = master_down_interval(100)
    marker = "OK" if high_priority_interval == 3007 and low_priority_interval == 3609 else "NG"
    print(
        f"[{marker}] priority 254 -> {high_priority_interval}ms, "
        f"priority 100 -> {low_priority_interval}ms (best backup moves first)"
    )
    marker = "OK" if high_priority_interval < low_priority_interval else "NG"
    print(f"[{marker}] 254's interval is shorter than 100's -> {high_priority_interval} < {low_priority_interval}")

    # --- The boundary is >=, so one ms before the threshold the master is still "up" ---
    watch = BackupWatch(last_heard_at=0)
    boundary = master_down_interval(254)

    just_before = master_is_down(watch, priority=254, now=boundary - 1)
    marker = "OK" if just_before is False else "NG"
    print(f"[{marker}] one ms before {boundary}ms threshold -> master_is_down={just_before}")

    exactly_at = master_is_down(watch, priority=254, now=boundary)
    marker = "OK" if exactly_at is True else "NG"
    print(f"[{marker}] exactly at {boundary}ms threshold    -> master_is_down={exactly_at}")

    # --- A heartbeat resets the silence clock, pushing the threshold forward ---
    heartbeat(watch, now=2000)
    marker = "OK" if watch.last_heard_at == 2000 else "NG"
    print(f"[{marker}] heartbeat at t=2000ms resets watch -> last_heard_at={watch.last_heard_at}")

    still_up_after_heartbeat = master_is_down(watch, priority=254, now=boundary)
    marker = "OK" if still_up_after_heartbeat is False else "NG"
    print(
        f"[{marker}] old boundary ({boundary}ms) no longer trips it -> "
        f"master_is_down={still_up_after_heartbeat}"
    )

    new_boundary = watch.last_heard_at + master_down_interval(254)
    now_it_trips = master_is_down(watch, priority=254, now=new_boundary)
    marker = "OK" if now_it_trips is True else "NG"
    print(f"[{marker}] new boundary ({new_boundary}ms) trips it     -> master_is_down={now_it_trips}")

    marker = "OK" if ADVERTISEMENT_INTERVAL == 1000 else "NG"
    print(f"[{marker}] ADVERTISEMENT_INTERVAL is {ADVERTISEMENT_INTERVAL}ms (RFC 5798 default)")


if __name__ == "__main__":
    main()
