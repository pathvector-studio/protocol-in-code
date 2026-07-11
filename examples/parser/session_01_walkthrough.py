from protocol_in_code.parser.ethernet import (
    HEADER_LEN,
    EthernetOutcome,
    format_mac,
    parse_ethernet,
)


def main() -> None:
    print("Session 01 walkthrough: Bytes have a shape")
    print()

    # Hand-built 14-byte Ethernet header + a short payload.
    # dst = aa:bb:cc:dd:ee:ff, src = 11:22:33:44:55:66, ethertype = 0x0800 (IPv4)
    dst_mac = bytes.fromhex("aabbccddeeff")
    src_mac = bytes.fromhex("112233445566")
    ethertype = bytes.fromhex("0800")
    payload = b"HELLOPAYLOAD"
    frame = dst_mac + src_mac + ethertype + payload

    parsed = parse_ethernet(frame)
    marker = "OK" if parsed.outcome is EthernetOutcome.OK else "NG"
    print(f"[{marker}] 14-byte header parses     -> {parsed.outcome.value}")

    marker = "OK" if parsed.header is not None and parsed.header.dst_mac == "aa:bb:cc:dd:ee:ff" else "NG"
    print(f"[{marker}] dst_mac reads correctly   -> {parsed.header.dst_mac}")

    marker = "OK" if parsed.header is not None and parsed.header.src_mac == "11:22:33:44:55:66" else "NG"
    print(f"[{marker}] src_mac reads correctly   -> {parsed.header.src_mac}")

    marker = "OK" if parsed.header is not None and parsed.header.ethertype == 0x0800 else "NG"
    print(f"[{marker}] ethertype reads correctly -> 0x{parsed.header.ethertype:04x}")

    marker = "OK" if parsed.payload == payload else "NG"
    print(f"[{marker}] payload starts at byte 14 -> {parsed.payload!r}")

    too_short = frame[: HEADER_LEN - 1]
    short_parsed = parse_ethernet(too_short)
    marker = "OK" if short_parsed.outcome is EthernetOutcome.TOO_SHORT else "NG"
    print(f"[{marker}] 13-byte frame is too short -> {short_parsed.outcome.value}")

    marker = "OK" if short_parsed.header is None else "NG"
    print(f"[{marker}] too-short parse has no header -> {short_parsed.header}")

    mac_shape = format_mac(bytes.fromhex("0a1b2c3d4e5f"))
    marker = "OK" if mac_shape == "0a:1b:2c:3d:4e:5f" else "NG"
    print(f"[{marker}] format_mac output shape   -> {mac_shape}")


if __name__ == "__main__":
    main()
