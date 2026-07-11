from __future__ import annotations

# The checksum is arithmetic, not magic: RFC 1071 defines it as the
# ones-complement sum of 16-bit words, complemented at the end. No table,
# no library call — just addition with the carry folded back in.

WORD_MASK = 0xFFFF
VALID_SUM = 0xFFFF


def ones_complement_sum(data: bytes) -> int:
    """Add every 16-bit word with end-around carry, per RFC 1071 section 4.1."""
    padded = data if len(data) % 2 == 0 else data + b"\x00"  # odd length: pad with a zero byte

    total = 0
    for offset in range(0, len(padded), 2):
        word = int.from_bytes(padded[offset : offset + 2], "big")
        total += word
        # end-around carry: a carry out of bit 16 wraps back into bit 0
        total = (total & WORD_MASK) + (total >> 16)

    return total


def internet_checksum(data: bytes) -> int:
    """The checksum is the ones' complement of the ones-complement sum."""
    return ~ones_complement_sum(data) & WORD_MASK


def verify_checksum(header: bytes) -> bool:
    """Sum the header WITH its checksum field included; a valid header sums to all-ones."""
    return ones_complement_sum(header) == VALID_SUM
