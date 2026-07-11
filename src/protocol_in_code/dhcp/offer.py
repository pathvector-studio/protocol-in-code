from __future__ import annotations

from dataclasses import dataclass

from .discover import DhcpMessage, MessageType

OFFER_HOLD_SECONDS = 30


@dataclass(frozen=True)
class Offer:
    """A proposal, not a promise: the server has set the address aside, nothing more."""

    ip: str
    lease_seconds: int
    server_id: str
    made_at: int


def make_offer(ip: str, lease_seconds: int, server_id: str, now: int) -> Offer:
    """A server with a free address turns it into a time-stamped proposal."""
    return Offer(ip=ip, lease_seconds=lease_seconds, server_id=server_id, made_at=now)


def offer_is_stale(offer: Offer, now: int) -> bool:
    """An offer is a proposal with a deadline: an unclaimed offer expires so the pool
    address it set aside doesn't stay hostage to a client that never answers.
    """
    return now >= offer.made_at + OFFER_HOLD_SECONDS


def accept_offer(offer: Offer, client_mac: str, transaction_id: int) -> DhcpMessage:
    """Turn an accepted offer into the REQUEST that follows it.

    The REQUEST echoes back the offer's server_id and ip - that echo is the lesson.
    A client can receive several OFFERs (one per listening server) but picks only one,
    and it says which by quoting that server's identity in a message that is itself
    still broadcast. Every server on the segment hears the echo, so the servers that
    were NOT named know instantly that they lost and are free to release their hold.
    """
    return DhcpMessage(
        message_type=MessageType.REQUEST,
        transaction_id=transaction_id,
        client_mac=client_mac,
        server_id=offer.server_id,
        requested_ip=offer.ip,
    )
