from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .seqnum import seq_add, seq_lt


class DeliveryOutcome(str, Enum):
    DELIVERED = "Delivered"
    BUFFERED = "Buffered"
    DUPLICATE = "Duplicate"


@dataclass(frozen=True)
class DeliveryResult:
    outcome: DeliveryOutcome
    delivered_len: int
    new_rcv_nxt: int


@dataclass
class ReassemblyBuffer:
    rcv_nxt: int
    segments: dict[int, int] = field(default_factory=dict)


def deliver(buffer: ReassemblyBuffer, seq: int, payload_len: int) -> DeliveryResult:
    """Out of order is not lost: it waits in the buffer until the missing bytes fill the gap."""
    if payload_len <= 0 or seq_lt(seq, buffer.rcv_nxt):
        return DeliveryResult(DeliveryOutcome.DUPLICATE, 0, buffer.rcv_nxt)

    if seq != buffer.rcv_nxt:
        buffer.segments[seq] = payload_len
        return DeliveryResult(DeliveryOutcome.BUFFERED, 0, buffer.rcv_nxt)

    # This segment lands exactly at rcv_nxt: drain every contiguous run that follows it.
    delivered_len = payload_len
    buffer.rcv_nxt = seq_add(buffer.rcv_nxt, payload_len)

    while buffer.rcv_nxt in buffer.segments:
        run_len = buffer.segments.pop(buffer.rcv_nxt)
        delivered_len += run_len
        buffer.rcv_nxt = seq_add(buffer.rcv_nxt, run_len)

    return DeliveryResult(DeliveryOutcome.DELIVERED, delivered_len, buffer.rcv_nxt)
