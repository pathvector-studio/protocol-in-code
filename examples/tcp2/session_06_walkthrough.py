from protocol_in_code.tcp2.backlog import ListenBacklog
from protocol_in_code.tcp2.janitor_loop import (
    Event,
    EventKind,
    ToyConnectionJanitor,
    run_day_in_the_life,
)
from protocol_in_code.tcp2.keepalive import KEEPALIVE_COUNT, KEEPALIVE_IDLE, KEEPALIVE_INTERVAL


def main() -> None:
    print("Session 06 walkthrough: Build the toy connection janitor")
    print()

    backlog = ListenBacklog(syn_limit=3, accept_limit=10)
    janitor = ToyConnectionJanitor(backlog=backlog)

    # Two short connections that will land in TIME_WAIT, one connection that
    # goes quiet and will only be noticed by keepalive.
    events = (
        Event(EventKind.CONNECT_AND_CLOSE, ("10.0.0.1", 5555)),
        Event(EventKind.CONNECT_AND_CLOSE, ("10.0.0.2", 5555)),
        Event(EventKind.IDLE_SILENCE, ("10.0.0.3", 5555)),
    )
    run_day_in_the_life(janitor, events)

    both_in_time_wait = {("10.0.0.1", 5555), ("10.0.0.2", 5555)}.issubset(janitor.time_wait_entries)
    marker = "OK" if both_in_time_wait else "NG"
    print(f"[{marker}] two connections entered TIME_WAIT -> {sorted(janitor.time_wait_entries)}")

    # TWO_MSL is 240 in this course's clock; ticking to clock=300 crosses it.
    janitor.tick(300)
    time_wait_line = f"clock={janitor.clock}: TIME_WAIT expired for 2 connection(s), freed ports"
    freed_ports = any(line.startswith(time_wait_line) for line in janitor.trace)
    marker = "OK" if freed_ports and janitor.clock == 300 else "NG"
    print(f"[{marker}] TIME_WAIT expiry frees 2 ports at clock=300")

    marker = "OK" if not janitor.time_wait_entries else "NG"
    print(f"[{marker}] time_wait_entries empty after expiry -> {janitor.time_wait_entries}")

    # Walk the idle connection's keepalive schedule in KEEPALIVE_INTERVAL-sized
    # steps once probing starts, so no probe is skipped by a coarser tick. The
    # idle connection's last_activity is clock=0 (set when its final ACK moved
    # it to the accept queue, before the TIME_WAIT tick above), so land exactly
    # on clock=KEEPALIVE_IDLE first, accounting for the clock=300 already spent.
    janitor.tick(KEEPALIVE_IDLE - janitor.clock)
    for _ in range(KEEPALIVE_COUNT):
        janitor.tick(KEEPALIVE_INTERVAL)

    dead_line = "clock=7875: ('10.0.0.3', 5555) declared DEAD, keepalive exhausted"
    marker = "OK" if dead_line in janitor.trace and janitor.clock == 7875 else "NG"
    print(f"[{marker}] keepalive declares DEAD at clock=7875")

    # A SYN flood against the same syn_limit=3 backlog: the first three SYNs
    # queue normally and fill it, the fourth is the first one answered by
    # cookie-mode instead of being dropped.
    flood = Event(EventKind.SYN_FLOOD_BURST, ("203.0.113.9", 0), count=5)
    run_day_in_the_life(janitor, (flood,))

    cookie_line = f"clock={janitor.clock}: SYN from ('203.0.113.9', 0, 3) answered statelessly (cookie-mode)"
    marker = "OK" if cookie_line in janitor.trace and janitor.cookie_mode else "NG"
    print(f"[{marker}] cookie-mode engages on the 4th SYN (syn_limit=3)")

    thesis = "none of this is the protocol"
    docstring = ToyConnectionJanitor.__doc__ or ""
    marker = "OK" if thesis in docstring.lower() else "NG"
    print(f"[{marker}] capstone thesis: \"{thesis} — it is the housekeeping the protocol leaves behind\"")


if __name__ == "__main__":
    main()
