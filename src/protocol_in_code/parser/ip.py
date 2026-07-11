from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Bits don't align to bytes. IPv4 packs a version and a header length into
# one byte, and three flag bits share a byte with a 13-bit fragment offset.
# Every extraction below is a shift or a mask naming the field it pulls out.
VERSION_IHL_OFFSET = 0
TOTAL_LENGTH_OFFSET = 2
IDENTIFICATION_OFFSET = 4
FLAGS_FRAGMENT_OFFSET = 6
TTL_OFFSET = 8
PROTOCOL_OFFSET = 9
CHECKSUM_OFFSET = 10
SRC_OFFSET = 12
DST_OFFSET = 16
MIN_HEADER_LEN = 20

IPV4_VERSION = 4
DF_BIT = 0x4000  # bit 14 of the flags/fragment-offset half-word
MF_BIT = 0x2000  # bit 13 of the flags/fragment-offset half-word
FRAGMENT_OFFSET_MASK = 0x1FFF  # low 13 bits: the fragment offset, in 8-byte units


class Ipv4Outcome(str, Enum):
    OK = "Ok"
    TOO_SHORT = "TooShort"
    NOT_IPV4 = "NotIpv4"
    BAD_IHL = "BadIhl"


@dataclass(frozen=True)
class Ipv4Header:
    version: int
    ihl: int
    total_length: int
    identification: int
    dont_fragment: bool
    more_fragments: bool
    fragment_offset: int
    ttl: int
    protocol: int
    checksum_field: int
    src: str
    dst: str
    header_len_bytes: int


@dataclass(frozen=True)
class Ipv4Parse:
    outcome: Ipv4Outcome
    header: Ipv4Header | None
    payload: bytes


def format_ipv4(raw: bytes) -> str:
    """Four bytes become the dotted-quad spelling everyone recognizes: 1.2.3.4."""
    return ".".join(str(byte) for byte in raw)


def parse_ipv4(packet: bytes) -> Ipv4Parse:
    """Split the version/IHL byte, then the flags/fragment-offset half-word, then trust the IHL."""
    if len(packet) < MIN_HEADER_LEN:
        return Ipv4Parse(Ipv4Outcome.TOO_SHORT, None, b"")

    version_ihl = packet[VERSION_IHL_OFFSET]
    version = version_ihl >> 4  # top nibble: IP version
    ihl = version_ihl & 0x0F  # bottom nibble: header length, in 4-byte words

    if version != IPV4_VERSION:
        return Ipv4Parse(Ipv4Outcome.NOT_IPV4, None, b"")

    header_len_bytes = ihl * 4  # IHL counts 32-bit words, not bytes
    if ihl < 5 or header_len_bytes > len(packet):
        # ihl > 5 means options follow the fixed fields; we acknowledge them
        # by trusting header_len_bytes for the payload slice below.
        return Ipv4Parse(Ipv4Outcome.BAD_IHL, None, b"")

    total_length = int.from_bytes(packet[TOTAL_LENGTH_OFFSET : TOTAL_LENGTH_OFFSET + 2], "big")
    identification = int.from_bytes(packet[IDENTIFICATION_OFFSET : IDENTIFICATION_OFFSET + 2], "big")

    flags_fragment = int.from_bytes(packet[FLAGS_FRAGMENT_OFFSET : FLAGS_FRAGMENT_OFFSET + 2], "big")
    dont_fragment = bool(flags_fragment & DF_BIT)
    more_fragments = bool(flags_fragment & MF_BIT)
    fragment_offset = flags_fragment & FRAGMENT_OFFSET_MASK

    ttl = packet[TTL_OFFSET]
    protocol = packet[PROTOCOL_OFFSET]
    checksum_field = int.from_bytes(packet[CHECKSUM_OFFSET : CHECKSUM_OFFSET + 2], "big")
    src = format_ipv4(packet[SRC_OFFSET : SRC_OFFSET + 4])
    dst = format_ipv4(packet[DST_OFFSET : DST_OFFSET + 4])

    header = Ipv4Header(
        version=version,
        ihl=ihl,
        total_length=total_length,
        identification=identification,
        dont_fragment=dont_fragment,
        more_fragments=more_fragments,
        fragment_offset=fragment_offset,
        ttl=ttl,
        protocol=protocol,
        checksum_field=checksum_field,
        src=src,
        dst=dst,
        header_len_bytes=header_len_bytes,
    )
    return Ipv4Parse(Ipv4Outcome.OK, header, packet[header_len_bytes:])
