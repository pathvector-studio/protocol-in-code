from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# "The backlog" sounds like one setting; it is two queues with different owners,
# different limits, and different failure modes:
#   - syn_queue: half-open connections (SYN seen, SYN-ACK sent, no final ACK yet).
#     The KERNEL fills this on every inbound SYN and drains it on the final ACK.
#   - accept_queue: fully-established connections waiting for accept() to claim them.
#     The kernel fills this on the final ACK and the APPLICATION drains it by calling
#     accept(). If the application is slow, this queue backs up independently of
#     whatever is happening to the syn_queue.
# Time here is a plain `now: int` tick, unused by this file's own logic (nothing here
# times out) but threaded through on_syn for parity with the rest of the course and
# for janitor_loop.py, which does use it.


class SynOutcome(str, Enum):
    QUEUED = "Queued"
    DROPPED_SYN_QUEUE_FULL = "DroppedSynQueueFull"


class AckOutcome(str, Enum):
    MOVED_TO_ACCEPT_QUEUE = "MovedToAcceptQueue"
    ACCEPT_QUEUE_FULL = "AcceptQueueFull"
    UNKNOWN_CLIENT = "UnknownClient"


@dataclass
class ListenBacklog:
    """One listening socket's state: half-open connections on one side, accepted ones on the other."""

    syn_limit: int
    accept_limit: int
    syn_queue: dict[tuple, int] = field(default_factory=dict)
    accept_queue: list = field(default_factory=list)


def on_syn(backlog: ListenBacklog, client_tuple: tuple, now: int) -> SynOutcome:
    """A SYN arrives: queue a half-open entry, or drop it if the syn_queue is already full.

    Real kernels do not actually drop here once the syn_queue fills - they switch to
    SYN cookies (syn_cookies.py) and stop tracking the half-open connection at all,
    answering statelessly instead. This toy models the naive fixed-size queue on
    purpose, to make the "queue is full" moment visible; janitor_loop.py is where the
    two files meet and cookie-mode kicks in instead of a drop.
    """
    if client_tuple in backlog.syn_queue:
        return SynOutcome.QUEUED

    if len(backlog.syn_queue) >= backlog.syn_limit:
        return SynOutcome.DROPPED_SYN_QUEUE_FULL

    backlog.syn_queue[client_tuple] = now
    return SynOutcome.QUEUED


def on_final_ack(backlog: ListenBacklog, client_tuple: tuple) -> AckOutcome:
    """The handshake's third packet arrives: promote the half-open entry to the accept queue.

    What real kernels do when the accept queue is already full at this moment: Linux
    silently drops the final ACK rather than resetting the connection - the half-open
    entry stays in the syn_queue, the client's ACK is simply not answered, and the
    client's own retransmit timer is what eventually gets it another try (by which
    time the application may have drained the accept queue). This function documents
    and implements that choice: on ACCEPT_QUEUE_FULL, the syn_queue entry is left in
    place, untouched, exactly as if the ACK had never arrived.
    """
    if client_tuple not in backlog.syn_queue:
        return AckOutcome.UNKNOWN_CLIENT

    if len(backlog.accept_queue) >= backlog.accept_limit:
        return AckOutcome.ACCEPT_QUEUE_FULL

    del backlog.syn_queue[client_tuple]
    backlog.accept_queue.append(client_tuple)
    return AckOutcome.MOVED_TO_ACCEPT_QUEUE


def app_accept(backlog: ListenBacklog) -> tuple | None:
    """The application calls accept(): pop the oldest fully-established connection, if any."""
    if not backlog.accept_queue:
        return None
    return backlog.accept_queue.pop(0)
