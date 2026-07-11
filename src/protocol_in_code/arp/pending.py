from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# The thesis: the IP layer doesn't block on ARP. A packet to an unresolved
# destination doesn't stall the sender waiting for a who-has/is-at exchange —
# it parks in a per-destination line while resolution runs, and either rides
# out with the answer or gets dropped if resolution fails.

MAX_QUEUE_PER_IP = 3


class EnqueueOutcome(str, Enum):
    QUEUED = "Queued"
    QUEUED_DROPPED_OLDEST = "QueuedDroppedOldest"


@dataclass
class PendingQueue:
    waiting: dict[str, tuple[str, ...]] = field(default_factory=dict)


def enqueue(queue: PendingQueue, ip: str, packet_label: str) -> EnqueueOutcome:
    """Park one more packet behind an unresolved IP; a full line drops its oldest member."""
    current = queue.waiting.get(ip, ())
    updated = current + (packet_label,)

    if len(updated) > MAX_QUEUE_PER_IP:
        updated = updated[-MAX_QUEUE_PER_IP:]
        queue.waiting[ip] = updated
        return EnqueueOutcome.QUEUED_DROPPED_OLDEST

    queue.waiting[ip] = updated
    return EnqueueOutcome.QUEUED


def flush(queue: PendingQueue, ip: str) -> tuple[str, ...]:
    """Resolution completed: hand back everything that was waiting, and clear the line."""
    waiting = queue.waiting.pop(ip, ())
    return waiting


def drop_all(queue: PendingQueue, ip: str) -> None:
    """Resolution failed: nothing is deliverable, so the line for this IP is discarded."""
    queue.waiting.pop(ip, None)
