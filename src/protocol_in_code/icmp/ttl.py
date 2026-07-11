from __future__ import annotations

from enum import Enum

from .message import IcmpMessage, IcmpType, QuotedPacket


class HopOutcome(str, Enum):
    FORWARDED = "Forwarded"
    EXPIRED = "Expired"


def decrement_and_decide(ttl: int) -> tuple[int, HopOutcome]:
    """TTL is a hop budget: every router spends one before deciding whether to keep going."""
    remaining = ttl - 1
    if remaining == 0:
        return remaining, HopOutcome.EXPIRED
    return remaining, HopOutcome.FORWARDED


def expire(quoted: QuotedPacket, router_name: str) -> IcmpMessage:
    """The router that spent the last hop reports back with the packet it killed."""
    return IcmpMessage(
        icmp_type=IcmpType.TIME_EXCEEDED,
        code=f"TTL expired in transit at {router_name}",
        quoted=quoted,
    )
