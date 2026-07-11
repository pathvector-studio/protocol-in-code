from protocol_in_code.parser.dispatch import ETHERTYPES, LayerId, next_layer, transport_protocol


def main() -> None:
    print("Session 02 walkthrough: Peel one layer, find the next")
    print()

    ipv4 = next_layer(0x0800)
    marker = "OK" if ipv4 is LayerId.IPV4 else "NG"
    print(f"[{marker}] 0x0800 -> IPv4              -> {ipv4.value}")

    ipv6 = next_layer(0x86DD)
    marker = "OK" if ipv6 is LayerId.IPV6 else "NG"
    print(f"[{marker}] 0x86DD -> IPv6              -> {ipv6.value}")

    arp = next_layer(0x0806)
    marker = "OK" if arp is LayerId.ARP else "NG"
    print(f"[{marker}] 0x0806 -> ARP               -> {arp.value}")

    unmapped_ethertype = next_layer(0x88CC)
    marker = "OK" if unmapped_ethertype is LayerId.UNKNOWN else "NG"
    print(f"[{marker}] 0x88CC -> not in the dict   -> {unmapped_ethertype.value}")

    tcp = transport_protocol(6)
    marker = "OK" if tcp is LayerId.TCP else "NG"
    print(f"[{marker}] proto 6 -> TCP              -> {tcp.value}")

    udp = transport_protocol(17)
    marker = "OK" if udp is LayerId.UDP else "NG"
    print(f"[{marker}] proto 17 -> UDP             -> {udp.value}")

    unmapped_proto = transport_protocol(132)
    marker = "OK" if unmapped_proto is LayerId.UNKNOWN else "NG"
    print(f"[{marker}] proto 132 -> not in the dict -> {unmapped_proto.value}")

    # next_layer() does nothing next_layer() couldn't do inline: it is
    # ETHERTYPES.get(key) with an UNKNOWN fallback, and nothing else.
    is_just_a_dict = next_layer(0x0800) is LayerId(ETHERTYPES[0x0800])
    marker = "OK" if is_just_a_dict else "NG"
    print(f"[{marker}] dispatch is table lookup   -> {is_just_a_dict}")


if __name__ == "__main__":
    main()
