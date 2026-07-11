from protocol_in_code.tcp.window import AcceptOutcome, ReceiveBuffer, accept, advertised_window, application_read


def main() -> None:
    print("Session 04 walkthrough: The window is how much room you have")
    print()

    buffer = ReceiveBuffer(capacity=100)

    initial = advertised_window(buffer)
    marker = "OK" if initial == 100 else "NG"
    print(f"[{marker}] empty buffer, full window   -> {initial}")

    first_outcome = accept(buffer, 40)
    after_first = advertised_window(buffer)
    marker = "OK" if first_outcome is AcceptOutcome.ACCEPTED and after_first == 60 else "NG"
    print(f"[{marker}] accept 40 bytes             -> {first_outcome.value}, window now {after_first}")

    second_outcome = accept(buffer, 50)
    after_second = advertised_window(buffer)
    marker = "OK" if second_outcome is AcceptOutcome.ACCEPTED and after_second == 10 else "NG"
    print(f"[{marker}] accept 50 more bytes        -> {second_outcome.value}, window now {after_second}")

    trimmed_outcome = accept(buffer, 30)
    after_trim = advertised_window(buffer)
    marker = "OK" if trimmed_outcome is AcceptOutcome.TRIMMED and after_trim == 0 else "NG"
    print(f"[{marker}] send 30, only 10 fits        -> {trimmed_outcome.value}, window now {after_trim}")

    refused_outcome = accept(buffer, 1)
    marker = "OK" if refused_outcome is AcceptOutcome.REFUSED else "NG"
    print(f"[{marker}] window is zero, refuse       -> {refused_outcome.value}")

    freed = application_read(buffer, 25)
    after_read = advertised_window(buffer)
    marker = "OK" if freed == 25 and after_read == 25 else "NG"
    print(f"[{marker}] application reads 25 bytes   -> freed {freed}, window now {after_read}")

    reopened_outcome = accept(buffer, 20)
    after_reopen = advertised_window(buffer)
    marker = "OK" if reopened_outcome is AcceptOutcome.ACCEPTED and after_reopen == 5 else "NG"
    print(f"[{marker}] window reopened, accept 20   -> {reopened_outcome.value}, window now {after_reopen}")

    drained = application_read(buffer, 1000)
    fully_open = advertised_window(buffer)
    marker = "OK" if drained == 95 and fully_open == 100 else "NG"
    print(f"[{marker}] read past buffered, capped   -> freed {drained}, window now {fully_open}")


if __name__ == "__main__":
    main()
