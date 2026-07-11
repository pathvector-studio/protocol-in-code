from protocol_in_code.parser.dispatch import LayerId
from protocol_in_code.parser.pcap_loop import GLOBAL_HEADER_LEN, build_test_pcap, read_pcap


def main() -> None:
    print("Session 05 walkthrough: Build the toy pcap reader")
    print()

    data = build_test_pcap()
    result = read_pcap(data)

    gh = result.global_header
    marker = "OK" if gh is not None and (gh.version_major, gh.version_minor) == (2, 4) else "NG"
    print(f"[{marker}] global header version     -> {gh.version_major}.{gh.version_minor}")

    marker = "OK" if gh is not None and gh.network == 1 else "NG"
    print(f"[{marker}] global header linktype    -> {gh.network} (Ethernet)")

    marker = "OK" if len(result.packets) == 2 else "NG"
    print(f"[{marker}] two packets in the file   -> {len(result.packets)}")

    packet_0 = result.packets[0]
    walked = (
        packet_0.ethernet is not None
        and packet_0.ip is not None
        and packet_0.transport is LayerId.TCP
        and packet_0.checksum_ok is True
    )
    marker = "OK" if walked else "NG"
    print(f"[{marker}] packet 0 walks eth->IPv4->TCP, checksum valid -> {packet_0.checksum_ok}")

    packet_1 = result.packets[1]
    stopped = packet_1.ethernet is not None and packet_1.ip is None
    marker = "OK" if stopped else "NG"
    print(f"[{marker}] packet 1 is ARP, dispatch stopped the walk -> ip is {packet_1.ip}")

    byte_order_line = any("magic identifies little-endian file" in line for line in result.trace)
    marker = "OK" if byte_order_line else "NG"
    print(f"[{marker}] trace names the byte order -> {[l for l in result.trace if 'magic' in l][0]}")

    # Corrupt the magic bytes: _detect_byte_order() returns None for both
    # interpretations, so read_pcap() bails out before reading any field.
    corrupt_magic = b"\x00\x00\x00\x00" + data[4:]
    bad_magic_result = read_pcap(corrupt_magic)
    marker = "OK" if bad_magic_result.global_header is None and bad_magic_result.packets == () else "NG"
    print(f"[{marker}] corrupt magic -> BadMagic  -> trace: {bad_magic_result.trace}")

    # Truncated before the 24-byte global header even completes.
    truncated_global = data[: GLOBAL_HEADER_LEN - 1]
    short_result = read_pcap(truncated_global)
    marker = "OK" if short_result.trace == ("global header: TooShort",) else "NG"
    print(f"[{marker}] truncated global header    -> trace: {short_result.trace}")

    # Truncated mid-record: global header is fine, but the first record's
    # 16-byte record header does not fully fit -- the loop stops, keeping
    # whatever packets it already parsed.
    truncated_record = data[: GLOBAL_HEADER_LEN + 5]
    partial_result = read_pcap(truncated_record)
    marker = "OK" if partial_result.trace[-1] == "record at 24: TooShortForRecordHeader" else "NG"
    print(f"[{marker}] truncated record header    -> trace: {partial_result.trace[-1]}")


if __name__ == "__main__":
    main()
