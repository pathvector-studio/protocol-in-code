from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# A header is nothing but an agreement about which byte lives where.
# These offsets ARE the Ethernet header; there is no other definition.
DST_OFFSET = 0
SRC_OFFSET = 6
TYPE_OFFSET = 12
HEADER_LEN = 14

MAC_LEN = 6


class EthernetOutcome(str, Enum):
    OK = "Ok"
    TOO_SHORT = "TooShort"


@dataclass(frozen=True)
class EthernetHeader:
    dst_mac: str
    src_mac: str
    ethertype: int


@dataclass(frozen=True)
class EthernetParse:
    outcome: EthernetOutcome
    header: EthernetHeader | None
    payload: bytes


def format_mac(raw: bytes) -> str:
    """Six bytes become the colon-hex spelling everyone recognizes: aa:bb:cc:dd:ee:ff."""
    return ":".join(f"{byte:02x}" for byte in raw)


def parse_ethernet(frame: bytes) -> EthernetParse:
    """Slice the fixed 14-byte header off the front; everything after it is the next layer's problem."""
    if len(frame) < HEADER_LEN:
        return EthernetParse(EthernetOutcome.TOO_SHORT, None, b"")

    dst_mac = format_mac(frame[DST_OFFSET : DST_OFFSET + MAC_LEN])
    src_mac = format_mac(frame[SRC_OFFSET : SRC_OFFSET + MAC_LEN])
    ethertype = int.from_bytes(frame[TYPE_OFFSET : TYPE_OFFSET + 2], byteorder="big")

    header = EthernetHeader(dst_mac=dst_mac, src_mac=src_mac, ethertype=ethertype)
    return EthernetParse(EthernetOutcome.OK, header, frame[HEADER_LEN:])
