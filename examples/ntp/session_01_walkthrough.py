from protocol_in_code.ntp.offset import Exchange, ExchangeValidity, delay, offset, validate_exchange


def main() -> None:
    print("Session 01 walkthrough: Four timestamps, two unknowns")
    print()

    hand = Exchange(t1=1000, t2=1005, t3=1006, t4=1012)
    computed_offset = offset(hand)
    computed_delay = delay(hand)
    marker = "OK" if computed_offset == -0.5 else "NG"
    print(f"[{marker}] offset ((1005-1000)+(1006-1012))/2 -> {computed_offset}")
    marker = "OK" if computed_delay == 11 else "NG"
    print(f"[{marker}] delay (1012-1000)-(1006-1005)      -> {computed_delay}")
    marker = "OK" if validate_exchange(hand) is ExchangeValidity.VALID else "NG"
    print(f"[{marker}] hand-computed exchange is valid    -> {validate_exchange(hand).value}")

    symmetric = Exchange(t1=1000, t2=1010, t3=1011, t4=1021)
    marker = "OK" if offset(symmetric) == 0.0 else "NG"
    print(f"[{marker}] symmetric zero-offset exchange     -> offset={offset(symmetric)}")

    client_late = Exchange(t1=1000, t2=1005, t3=1006, t4=900)
    marker = "OK" if validate_exchange(client_late) is ExchangeValidity.MALFORMED else "NG"
    print(f"[{marker}] t4 before t1 (client receive early) -> {validate_exchange(client_late).value}")

    server_backwards = Exchange(t1=1000, t2=1010, t3=1006, t4=1012)
    marker = "OK" if validate_exchange(server_backwards) is ExchangeValidity.MALFORMED else "NG"
    print(f"[{marker}] t3 before t2 (server sent before recv) -> {validate_exchange(server_backwards).value}")

    slow_return = Exchange(t1=1000, t2=1008, t3=1009, t4=1030)
    marker = "OK" if offset(slow_return) == -6.5 else "NG"
    print(f"[{marker}] asymmetric-looking exchange still computes -> offset={offset(slow_return)}")


if __name__ == "__main__":
    main()
