from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MessageType(str, Enum):
    DISCOVER = "Discover"
    OFFER = "Offer"
    REQUEST = "Request"
    ACK = "Ack"
    NAK = "Nak"


class MessageValidity(str, Enum):
    MISSING_OFFERED_IP = "MissingOfferedIp"
    MISSING_SERVER_ID = "MissingServerId"
    VALID = "Valid"


@dataclass(frozen=True)
class DhcpMessage:
    """One packet on the wire, wide enough to hold every field any DORA step might need."""

    message_type: MessageType
    transaction_id: int
    client_mac: str
    offered_ip: str | None = None
    server_id: str | None = None
    requested_ip: str | None = None


def make_discover(client_mac: str, transaction_id: int) -> DhcpMessage:
    """Discovery is shouting into the dark: a client with no address, no server, nothing to lose.

    There is no destination field here on purpose - the client doesn't know a server's
    address yet, so it can't address one. Modeling "broadcast" as an absent destination
    is the lesson: this message goes out as broadcast because it has nowhere else to go.
    """
    return DhcpMessage(
        message_type=MessageType.DISCOVER,
        transaction_id=transaction_id,
        client_mac=client_mac,
    )


def validate_message(msg: DhcpMessage) -> MessageValidity:
    """Check that a message carries the fields its own type promises to carry."""
    if msg.message_type is MessageType.OFFER and msg.offered_ip is None:
        return MessageValidity.MISSING_OFFERED_IP

    if msg.message_type is MessageType.REQUEST and msg.server_id is None:
        return MessageValidity.MISSING_SERVER_ID

    if msg.message_type is MessageType.ACK and msg.offered_ip is None:
        return MessageValidity.MISSING_OFFERED_IP

    return MessageValidity.VALID
