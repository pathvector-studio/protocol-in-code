from protocol_in_code.icmp.message import IcmpType
from protocol_in_code.icmp.probing import Hop, Path, probe
from protocol_in_code.icmp.unreachable import UnreachableCode


def main() -> None:
    print("Session 04 walkthrough: Time exceeded draws the map")
    print()

    path = Path(
        hops=(
            Hop(router_name="r1", responds=True),
            Hop(router_name="r2", responds=False),
            Hop(router_name="r3", responds=True),
        ),
        destination="10.0.0.99",
    )

    first_hop = probe(path, ttl=1, dst_port=33434)
    marker = "OK" if (
        first_hop.answerer == "r1"
        and first_hop.message is not None
        and first_hop.message.icmp_type is IcmpType.TIME_EXCEEDED
    ) else "NG"
    print(f"[{marker}] ttl=1 -> first hop confesses -> {first_hop.answerer} {first_hop.message.icmp_type.value}")

    silent_hop = probe(path, ttl=2, dst_port=33434)
    marker = "OK" if silent_hop.answerer is None and silent_hop.message is None else "NG"
    print(f"[{marker}] ttl=2 -> second hop is silent -> answerer={silent_hop.answerer}")

    third_hop = probe(path, ttl=3, dst_port=33434)
    marker = "OK" if (
        third_hop.answerer == "r3"
        and third_hop.message is not None
        and third_hop.message.icmp_type is IcmpType.TIME_EXCEEDED
    ) else "NG"
    print(f"[{marker}] ttl=3 -> third hop confesses  -> {third_hop.answerer} {third_hop.message.icmp_type.value}")

    past_the_end = probe(path, ttl=4, dst_port=33434)
    marker = "OK" if (
        past_the_end.answerer == path.destination
        and past_the_end.message is not None
        and past_the_end.message.icmp_type is IcmpType.DEST_UNREACHABLE
        and past_the_end.message.code == UnreachableCode.PORT_UNREACHABLE.value
    ) else "NG"
    print(f"[{marker}] ttl=4 -> destination's error is the success -> {past_the_end.answerer} {past_the_end.message.code}")

    quoted_dst_port = past_the_end.message.quoted.dst_port
    marker = "OK" if quoted_dst_port == 33434 else "NG"
    print(f"[{marker}] the quoted packet still names the probe's dst_port -> {quoted_dst_port}")

    well_past_the_end = probe(path, ttl=30, dst_port=33434)
    marker = "OK" if well_past_the_end.answerer == path.destination else "NG"
    print(f"[{marker}] ttl=30 (way past the path) -> still the destination -> {well_past_the_end.answerer}")


if __name__ == "__main__":
    main()
