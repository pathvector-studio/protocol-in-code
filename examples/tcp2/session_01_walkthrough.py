from protocol_in_code.tcp2.time_wait_cost import (
    EPHEMERAL_PORTS,
    connect_would_fail,
    max_rate_to_one_destination,
    time_wait_slots,
)
from protocol_in_code.tcp.teardown import TWO_MSL


def main() -> None:
    print("Session 01 walkthrough: TIME_WAIT is a promise with a price")
    print()

    headline = max_rate_to_one_destination()
    by_hand = EPHEMERAL_PORTS / TWO_MSL
    marker = "OK" if headline == by_hand else "NG"
    print(f"[{marker}] {EPHEMERAL_PORTS}/{TWO_MSL} = {by_hand:.2f}/tick -> max_rate_to_one_destination() = {headline:.2f}")

    slots_at_headline = time_wait_slots(headline)
    marker = "OK" if slots_at_headline == EPHEMERAL_PORTS else "NG"
    print(f"[{marker}] time_wait_slots({headline:.2f}) at the ceiling rate -> {slots_at_headline} slots (== {EPHEMERAL_PORTS} ports)")

    half_rate = headline / 2
    slots_at_half = time_wait_slots(half_rate)
    marker = "OK" if slots_at_half == EPHEMERAL_PORTS // 2 else "NG"
    print(f"[{marker}] time_wait_slots({half_rate:.2f}) at half the rate -> {slots_at_half} slots (half of {EPHEMERAL_PORTS})")

    double_rate = headline
    slots_at_double = time_wait_slots(double_rate * 2)
    marker = "OK" if slots_at_double == slots_at_half * 4 else "NG"
    print(f"[{marker}] double the rate ({half_rate:.2f} -> {half_rate*2:.2f}) roughly doubles the slots -> {slots_at_half} -> {time_wait_slots(half_rate*2)}")

    below_ceiling = EPHEMERAL_PORTS - 1
    result = connect_would_fail(below_ceiling)
    marker = "OK" if result is False else "NG"
    print(f"[{marker}] connect_would_fail({below_ceiling}) one port free      -> {result}")

    at_ceiling = EPHEMERAL_PORTS
    result = connect_would_fail(at_ceiling)
    marker = "OK" if result is True else "NG"
    print(f"[{marker}] connect_would_fail({at_ceiling}) zero ports free     -> {result}")

    slow_rate = 1.0
    slow_slots = time_wait_slots(slow_rate)
    marker = "OK" if slow_slots == TWO_MSL else "NG"
    print(f"[{marker}] time_wait_slots(1.0) one connect/tick     -> {slow_slots} slots (== TWO_MSL={TWO_MSL})")


if __name__ == "__main__":
    main()
