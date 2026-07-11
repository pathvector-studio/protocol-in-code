from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

DUP_ACK_THRESHOLD = 3


class AckSignal(str, Enum):
    NEW_DATA_ACKED = "NewDataAcked"
    DUPLICATE = "Duplicate"
    FAST_RETRANSMIT = "FastRetransmit"


@dataclass
class AckTracker:
    last_ack: int = 0
    dup_count: int = 0


def on_ack(tracker: AckTracker, ack: int) -> AckSignal:
    """Three duplicates mean loss: the third repeat of the same ack triggers fast retransmit."""
    if ack != tracker.last_ack:
        tracker.last_ack = ack
        tracker.dup_count = 0
        return AckSignal.NEW_DATA_ACKED

    tracker.dup_count += 1

    if tracker.dup_count == DUP_ACK_THRESHOLD:
        return AckSignal.FAST_RETRANSMIT

    return AckSignal.DUPLICATE
