from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class IcmpType(str, Enum):
    ECHO_REQUEST = "Echo Request"
    ECHO_REPLY = "Echo Reply"
    DEST_UNREACHABLE = "Destination Unreachable"
    TIME_EXCEEDED = "Time Exceeded"


# The four ICMP types above split into two families: echo types carry a
# payload the sender invented (a ping body); error types carry no such
# thing — they carry a diagnosis instead. validate_message enforces that
# split.
ERROR_TYPES = frozenset({IcmpType.DEST_UNREACHABLE, IcmpType.TIME_EXCEEDED})


@dataclass(frozen=True)
class QuotedPacket:
    """An error is a packet about a packet.

    RFC 792 has every ICMP error quote the IP header plus the first 8 bytes
    of the original datagram's payload. That is not an arbitrary number:
    for TCP and UDP, the first 8 bytes of the payload are exactly the
    source and destination ports. Eight bytes is the minimum that still
    lets the sender map the error back to the socket that caused it —
    any less and the error would be undiagnosable noise.
    """

    src_ip: str
    dst_ip: str
    protocol: str
    src_port: int
    dst_port: int


@dataclass(frozen=True)
class IcmpMessage:
    icmp_type: IcmpType
    code: str
    quoted: QuotedPacket | None


def validate_message(message: IcmpMessage) -> bool:
    """Error types REQUIRE a quote; echo types must NOT carry one."""
    has_quote = message.quoted is not None
    if message.icmp_type in ERROR_TYPES:
        return has_quote
    return not has_quote
