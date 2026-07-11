from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .message import IcmpMessage, IcmpType, QuotedPacket


class UnreachableCode(str, Enum):
    NET_UNREACHABLE = "Network Unreachable"
    HOST_UNREACHABLE = "Host Unreachable"
    PORT_UNREACHABLE = "Port Unreachable"
    FRAG_NEEDED = "Fragmentation Needed"


# Unreachable has flavors, and the flavor names the sender. Net/host
# unreachable are reported by a router along the way that has no route
# left to try. Port unreachable is different in kind, not just degree:
# it means the packet ARRIVED — the destination host itself received it
# and found nobody listening on that port. Frag-needed comes from the
# router whose outbound link has a smaller MTU than the packet.
_SENDER_BY_CODE: dict[UnreachableCode, str] = {
    UnreachableCode.NET_UNREACHABLE: "a router along the path (no route to the network)",
    UnreachableCode.HOST_UNREACHABLE: "a router along the path (no route to the host)",
    UnreachableCode.PORT_UNREACHABLE: "the destination host itself (packet arrived, nobody listening)",
    UnreachableCode.FRAG_NEEDED: "the router whose next hop link is too small for the packet",
}


def who_sends(code: UnreachableCode) -> str:
    """Name the sender implied by the unreachable code, not just the code."""
    return _SENDER_BY_CODE[code]


def make_port_unreachable(quoted: QuotedPacket) -> IcmpMessage:
    """Port unreachable is the destination confessing: I got it, nobody was home."""
    return IcmpMessage(
        icmp_type=IcmpType.DEST_UNREACHABLE,
        code=UnreachableCode.PORT_UNREACHABLE.value,
        quoted=quoted,
    )


def make_frag_needed(quoted: QuotedPacket, next_hop_mtu: int) -> IcmpMessage:
    """Frag-needed rides an MTU value; that number is the whole PMTUD protocol.

    The sender reads next_hop_mtu out of the error and shrinks future
    packets to fit — Path MTU Discovery is nothing more than listening to
    this one number.
    """
    return IcmpMessage(
        icmp_type=IcmpType.DEST_UNREACHABLE,
        code=f"{UnreachableCode.FRAG_NEEDED.value} (next-hop MTU {next_hop_mtu})",
        quoted=quoted,
    )
