from protocol_in_code.ntp.client_loop import (
    MAX_SLEW_PER_ADJUST,
    ToySntpClient,
    apply_correction,
    best_sample,
    run_sync,
)
from protocol_in_code.ntp.client_loop import sample as take_sample
from protocol_in_code.ntp.offset import Exchange


def main() -> None:
    print("Session 04 walkthrough: Build the toy NTP client loop")
    print()

    filter_client = ToySntpClient()
    wide = Exchange(t1=1000, t2=1030, t3=1031, t4=1041)  # delay 40, offset +10
    narrow = Exchange(t1=1000, t2=1005, t3=1006, t4=1012)  # delay 11, offset -0.5
    widest = Exchange(t1=1000, t2=1050, t3=1051, t4=1120)  # delay 119
    for exchange in (wide, narrow, widest):
        take_sample(filter_client, exchange)

    winner = best_sample(filter_client)
    marker = "OK" if winner is not None and winner.delay_ms == 11 else "NG"
    print(f"[{marker}] three mixed-delay samples -> min delay wins -> delay={winner.delay_ms}ms")

    small_client = ToySntpClient()
    small_exchange = Exchange(t1=1000, t2=1030, t3=1031, t4=1041)  # offset +10
    small_sample = take_sample(small_client, small_exchange)
    apply_correction(small_client, small_sample)
    marker = "OK" if small_client.local_clock_ms == 10 else "NG"
    print(f"[{marker}] +10ms offset, well under the cap -> applied in full -> clock={small_client.local_clock_ms}ms")

    big_client = ToySntpClient()
    big_exchange = Exchange(t1=1000, t2=1600, t3=1601, t4=1201)  # offset +500
    big_sample = take_sample(big_client, big_exchange)
    marker = "OK" if big_sample.offset_ms == 500.0 else "NG"
    print(f"[{marker}] raw offset before clamping             -> offset={big_sample.offset_ms:+.1f}ms")
    apply_correction(big_client, big_sample)
    marker = "OK" if big_client.local_clock_ms == MAX_SLEW_PER_ADJUST else "NG"
    print(f"[{marker}] 500ms offset clamps to the slew cap    -> clock={big_client.local_clock_ms}ms")

    e2e_client = ToySntpClient()
    exchanges = (
        wide,  # delay 40
        narrow,  # delay 11, the eventual winner
        Exchange(t1=1000, t2=1005, t3=1006, t4=900),  # malformed: t4 < t1, rejected
    )
    chosen = run_sync(e2e_client, exchanges)
    marker = "OK" if chosen is not None and chosen.delay_ms == 11 else "NG"
    print(f"[{marker}] run_sync end-to-end -> chosen sample has minimum delay -> {chosen.delay_ms}ms")

    expected_line = "chosen: delay=11.0ms (minimum among valid samples)"
    marker = "OK" if expected_line in e2e_client.trace else "NG"
    print(f"[{marker}] trace records the chosen line          -> \"{expected_line}\"")

    marker = "OK" if any(line.startswith("rejected:") for line in e2e_client.trace) else "NG"
    print(f"[{marker}] trace also records the rejected exchange")


if __name__ == "__main__":
    main()
