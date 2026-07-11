from protocol_in_code.parser.checksum import internet_checksum, ones_complement_sum, verify_checksum


def main() -> None:
    print("Session 04 walkthrough: The checksum is arithmetic, not magic")
    print()

    # Three 16-bit words, no carry: 0x0001 + 0x0002 + 0x0003 = 0x0006 by hand.
    three_words = bytes.fromhex("000100020003")
    total = ones_complement_sum(three_words)
    marker = "OK" if total == 0x0006 else "NG"
    print(f"[{marker}] three words, no carry     -> 0x{total:04x}")

    # Odd length: one byte 0xFF is zero-padded to the word 0xFF00 before summing.
    odd_length = bytes([0xFF])
    padded_sum = ones_complement_sum(odd_length)
    marker = "OK" if padded_sum == 0xFF00 else "NG"
    print(f"[{marker}] odd length zero-padded    -> 0x{padded_sum:04x}")

    # End-around carry: 0xFFFF + 0x0001 overflows 16 bits; the carry wraps back to bit 0.
    carry_data = bytes.fromhex("FFFF0001")
    carried = ones_complement_sum(carry_data)
    marker = "OK" if carried == 0x0001 else "NG"
    print(f"[{marker}] end-around carry wraps    -> 0x{carried:04x}")

    # A real 20-byte IPv4 header (version/IHL, DSCP/ECN, total length, id,
    # flags/fragment offset, TTL, protocol, checksum placeholder, src, dst)
    # with the checksum field filled in by internet_checksum() itself.
    header_without_checksum = (
        bytes([0x45, 0x00])  # version 4, IHL 5; DSCP/ECN 0
        + (20).to_bytes(2, "big")  # total length
        + (0).to_bytes(2, "big")  # identification
        + (0x4000).to_bytes(2, "big")  # flags/fragment offset: DF set
        + bytes([64, 6])  # TTL 64, protocol 6 (TCP)
        + (0).to_bytes(2, "big")  # checksum placeholder
        + bytes([10, 0, 0, 1])  # src
        + bytes([10, 0, 0, 2])  # dst
    )
    checksum = internet_checksum(header_without_checksum)
    header = header_without_checksum[:10] + checksum.to_bytes(2, "big") + header_without_checksum[12:]

    marker = "OK" if verify_checksum(header) else "NG"
    print(f"[{marker}] real IPv4 header verifies -> checksum 0x{checksum:04x}")

    # The property that makes verify_checksum work at all: sum the header
    # WITH the checksum field included, and a valid header sums to all-ones.
    full_sum = ones_complement_sum(header)
    marker = "OK" if full_sum == 0xFFFF else "NG"
    print(f"[{marker}] full sum is all-ones      -> 0x{full_sum:04x}")

    flipped = bytearray(header)
    flipped[0] ^= 0xFF
    marker = "OK" if not verify_checksum(bytes(flipped)) else "NG"
    print(f"[{marker}] one flipped byte fails    -> {verify_checksum(bytes(flipped))}")


if __name__ == "__main__":
    main()
