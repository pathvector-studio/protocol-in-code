from protocol_in_code.icmp.message import IcmpType, QuotedPacket
from protocol_in_code.icmp.unreachable import (
    UnreachableCode,
    make_frag_needed,
    make_port_unreachable,
    who_sends,
)


def main() -> None:
    print("Session 02 walkthrough: Unreachable has flavors")
    print()

    net_sender = who_sends(UnreachableCode.NET_UNREACHABLE)
    marker = "OK" if "router" in net_sender else "NG"
    print(f"[{marker}] NET_UNREACHABLE sender        -> {net_sender}")

    host_sender = who_sends(UnreachableCode.HOST_UNREACHABLE)
    marker = "OK" if "router" in host_sender else "NG"
    print(f"[{marker}] HOST_UNREACHABLE sender       -> {host_sender}")

    port_sender = who_sends(UnreachableCode.PORT_UNREACHABLE)
    marker = "OK" if "destination host" in port_sender else "NG"
    print(f"[{marker}] PORT_UNREACHABLE from DEST    -> {port_sender}")

    frag_sender = who_sends(UnreachableCode.FRAG_NEEDED)
    marker = "OK" if "router" in frag_sender else "NG"
    print(f"[{marker}] FRAG_NEEDED sender            -> {frag_sender}")

    quote = QuotedPacket(
        src_ip="198.51.100.5",
        dst_ip="203.0.113.9",
        protocol="UDP",
        src_port=53421,
        dst_port=33434,
    )

    frag_needed = make_frag_needed(quote, next_hop_mtu=1400)
    mtu_carried = "1400" in frag_needed.code
    marker = "OK" if mtu_carried else "NG"
    print(f"[{marker}] frag-needed carries the mtu   -> {frag_needed.code}")

    port_unreachable = make_port_unreachable(quote)
    round_trips = (
        port_unreachable.icmp_type is IcmpType.DEST_UNREACHABLE
        and port_unreachable.code == UnreachableCode.PORT_UNREACHABLE.value
        and port_unreachable.quoted == quote
    )
    marker = "OK" if round_trips else "NG"
    print(f"[{marker}] port-unreachable quote round-trips -> {port_unreachable.quoted.dst_port}")


if __name__ == "__main__":
    main()
