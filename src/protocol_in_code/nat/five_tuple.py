from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# The kernel does not track "connections" - it tracks keys. Everything in this
# track (rewrite.py, table.py, ports.py, timeout.py, nat_loop.py) is built on
# the fact that a 5-tuple is just a hashable value, and NAT is what happens
# when you rewrite it and remember the rewrite.

MIN_PORT = 1
MAX_PORT = 65535
KNOWN_PROTOCOLS = ("tcp", "udp")


class TupleValidity(str, Enum):
    VALID = "Valid"
    UNKNOWN_PROTOCOL = "UnknownProtocol"
    BAD_SRC_PORT = "BadSrcPort"
    BAD_DST_PORT = "BadDstPort"


@dataclass(frozen=True)
class FiveTuple:
    """A connection is a 5-tuple: protocol plus both endpoints, nothing more."""

    protocol: str
    src_ip: str
    src_port: int
    dst_ip: str
    dst_port: int


def validate_tuple(t: FiveTuple) -> TupleValidity:
    """The table only ever indexes on tuples worth trusting; garbage in is rejected here, not downstream."""
    if t.protocol not in KNOWN_PROTOCOLS:
        return TupleValidity.UNKNOWN_PROTOCOL
    if not (MIN_PORT <= t.src_port <= MAX_PORT):
        return TupleValidity.BAD_SRC_PORT
    if not (MIN_PORT <= t.dst_port <= MAX_PORT):
        return TupleValidity.BAD_DST_PORT
    return TupleValidity.VALID


def reply_tuple(t: FiveTuple) -> FiveTuple:
    """The reply direction is just src and dst swapped - a pure transformation, not a lookup."""
    return FiveTuple(
        protocol=t.protocol,
        src_ip=t.dst_ip,
        src_port=t.dst_port,
        dst_ip=t.src_ip,
        dst_port=t.src_port,
    )
