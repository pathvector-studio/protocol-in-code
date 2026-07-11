from protocol_in_code.tcp2.nagle_delack import DELACK_TIMEOUT_MS, READ, simulate


def main() -> None:
    print("Session 03 walkthrough: Nagle and delayed ACK deadlock")
    print()

    deadlock = simulate((10, 20, READ), nodelay=False)
    marker = "OK" if deadlock.total_ms == DELACK_TIMEOUT_MS else "NG"
    print(f"[{marker}] write-write-read, Nagle+delack on      -> total_ms={deadlock.total_ms} (== {DELACK_TIMEOUT_MS})")

    held_event = f"write(20) held by nagle at 0ms, unacked segment in flight"
    marker = "OK" if held_event in deadlock.events else "NG"
    print(f"[{marker}] second write is held waiting for the first's ACK -> {held_event!r} in events")

    timeout_event = f"delayed-ack timeout fires at {DELACK_TIMEOUT_MS}ms, ack sent"
    marker = "OK" if timeout_event in deadlock.events else "NG"
    print(f"[{marker}] only the delack timer breaks the standoff -> {timeout_event!r} in events")

    nodelay = simulate((10, 20, READ), nodelay=True)
    marker = "OK" if nodelay.total_ms == 0 else "NG"
    print(f"[{marker}] same writes with TCP_NODELAY            -> total_ms={nodelay.total_ms} (== 0)")

    piggyback_event = "second segment lets receiver ack immediately at 0ms"
    marker = "OK" if piggyback_event in nodelay.events else "NG"
    print(f"[{marker}] second segment arrives immediately, ack piggybacks -> {piggyback_event!r} in events")

    single = simulate((10, READ), nodelay=False)
    marker = "OK" if single.total_ms == DELACK_TIMEOUT_MS else "NG"
    print(f"[{marker}] single write-read (no Nagle involved)  -> total_ms={single.total_ms} (delayed ACK alone still waits for the timer)")

    marker = "OK" if held_event not in single.events else "NG"
    print(f"[{marker}] no held-write event in the single-write case -> nothing for Nagle to hold")


if __name__ == "__main__":
    main()
