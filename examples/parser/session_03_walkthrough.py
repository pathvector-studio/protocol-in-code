from protocol_in_code.parser.ip import Ipv4Outcome, parse_ipv4


def ipv4_header(
    version_ihl: int,
    flags_fragment: int = 0x0000,
    protocol: int = 6,
    src: bytes = bytes([192, 0, 2, 1]),
    dst: bytes = bytes([192, 0, 2, 2]),
    options: bytes = b"",
) -> bytes:
    """Build a minimal IPv4 header byte-by-byte, field offset by field offset."""
    return (
        bytes([version_ihl, 0x00])  # version/IHL, DSCP+ECN (unused here)
        + (20).to_bytes(2, "big")  # total_length
        + (0x1234).to_bytes(2, "big")  # identification
        + flags_fragment.to_bytes(2, "big")  # flags + fragment offset
        + bytes([64, protocol])  # ttl, protocol
        + (0xABCD).to_bytes(2, "big")  # checksum (not validated by this parser)
        + src
        + dst
        + options
    )


def main() -> None:
    print("Session 03 walkthrough: Bits don't align to bytes")
    print()

    # 0x45 = version nibble 4, IHL nibble 5 -> header is 5 * 4 = 20 bytes.
    header_45 = ipv4_header(0x45)
    parsed_45 = parse_ipv4(header_45)
    marker = "OK" if parsed_45.outcome is Ipv4Outcome.OK and parsed_45.header.version == 4 else "NG"
    print(f"[{marker}] 0x45 -> version 4          -> {parsed_45.header.version}")

    marker = "OK" if parsed_45.header.ihl == 5 and parsed_45.header.header_len_bytes == 20 else "NG"
    print(f"[{marker}] 0x45 -> ihl 5, 20-byte hdr -> ihl={parsed_45.header.ihl} len={parsed_45.header.header_len_bytes}")

    # 0x46 = version 4, IHL 6 -> options present, header is 6 * 4 = 24 bytes.
    header_46 = ipv4_header(0x46, options=bytes(4))
    parsed_46 = parse_ipv4(header_46)
    marker = "OK" if parsed_46.outcome is Ipv4Outcome.OK and parsed_46.header.header_len_bytes == 24 else "NG"
    print(f"[{marker}] 0x46 -> 24-byte header     -> {parsed_46.header.header_len_bytes} (options acknowledged)")

    # Flags/fragment half-word with only DF set.
    df_only = ipv4_header(0x45, flags_fragment=0x4000)
    parsed_df = parse_ipv4(df_only)
    df_ok = parsed_df.header.dont_fragment is True and parsed_df.header.more_fragments is False
    df_ok = df_ok and parsed_df.header.fragment_offset == 0
    marker = "OK" if df_ok else "NG"
    print(f"[{marker}] DF set, MF clear, offset 0 -> df={parsed_df.header.dont_fragment} mf={parsed_df.header.more_fragments} off={parsed_df.header.fragment_offset}")

    # Top nibble 6 -> version 6, not this parser's business.
    header_v6 = ipv4_header(0x65)
    parsed_v6 = parse_ipv4(header_v6)
    marker = "OK" if parsed_v6.outcome is Ipv4Outcome.NOT_IPV4 and parsed_v6.header is None else "NG"
    print(f"[{marker}] 0x65 -> version 6 rejected -> {parsed_v6.outcome.value}")

    # IHL nibble 4 means a header shorter than the 20-byte minimum: invalid.
    header_bad_ihl = ipv4_header(0x44)
    parsed_bad_ihl = parse_ipv4(header_bad_ihl)
    marker = "OK" if parsed_bad_ihl.outcome is Ipv4Outcome.BAD_IHL and parsed_bad_ihl.header is None else "NG"
    print(f"[{marker}] 0x44 -> ihl 4 is bad       -> {parsed_bad_ihl.outcome.value}")

    # src/dst render as dotted quads.
    quads_ok = parsed_45.header.src == "192.0.2.1" and parsed_45.header.dst == "192.0.2.2"
    marker = "OK" if quads_ok else "NG"
    print(f"[{marker}] src/dst as dotted quads    -> {parsed_45.header.src} -> {parsed_45.header.dst}")


if __name__ == "__main__":
    main()
