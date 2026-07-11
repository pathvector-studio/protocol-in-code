from protocol_in_code.icmp.message import IcmpType, QuotedPacket
from protocol_in_code.icmp.ttl import HopOutcome, decrement_and_decide, expire


def main() -> None:
    print("Session 03 walkthrough: TTL is a hop budget")
    print()

    new_ttl, outcome = decrement_and_decide(3)
    marker = "OK" if new_ttl == 2 and outcome is HopOutcome.FORWARDED else "NG"
    print(f"[{marker}] ttl 3 at a router             -> {new_ttl} {outcome.value}")

    new_ttl, outcome = decrement_and_decide(1)
    marker = "OK" if new_ttl == 0 and outcome is HopOutcome.EXPIRED else "NG"
    print(f"[{marker}] ttl 1 at a router             -> {new_ttl} {outcome.value}")

    quote = QuotedPacket(
        src_ip="198.51.100.5",
        dst_ip="203.0.113.9",
        protocol="UDP",
        src_port=53421,
        dst_port=33434,
    )

    time_exceeded = expire(quote, router_name="core-router-3")
    carries_quote_and_name = (
        time_exceeded.icmp_type is IcmpType.TIME_EXCEEDED
        and time_exceeded.quoted == quote
        and "core-router-3" in time_exceeded.code
    )
    marker = "OK" if carries_quote_and_name else "NG"
    print(f"[{marker}] expire() carries quote+router -> {time_exceeded.code}")

    ttl = 4
    steps = 0
    outcome = HopOutcome.FORWARDED
    while outcome is HopOutcome.FORWARDED:
        ttl, outcome = decrement_and_decide(ttl)
        steps += 1
    marker = "OK" if steps == 4 and ttl == 0 and outcome is HopOutcome.EXPIRED else "NG"
    print(f"[{marker}] ttl 4 expires in exactly 4 hops -> {steps} steps, ttl {ttl}")


if __name__ == "__main__":
    main()
