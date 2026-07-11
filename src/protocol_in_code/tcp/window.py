from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AcceptOutcome(str, Enum):
    ACCEPTED = "Accepted"
    TRIMMED = "Trimmed"
    REFUSED = "Refused"


@dataclass
class ReceiveBuffer:
    capacity: int
    buffered: int = 0


def advertised_window(buffer: ReceiveBuffer) -> int:
    """The window is how much room you have: capacity minus what's already sitting there."""
    return max(0, buffer.capacity - buffer.buffered)


def accept(buffer: ReceiveBuffer, payload_len: int) -> AcceptOutcome:
    """Data only enters the buffer if the advertised window actually had room for it."""
    room = advertised_window(buffer)

    if room <= 0:
        return AcceptOutcome.REFUSED

    if payload_len <= room:
        buffer.buffered += payload_len
        return AcceptOutcome.ACCEPTED

    # The sender overshot the last-known window; take what fits and drop the rest.
    buffer.buffered += room
    return AcceptOutcome.TRIMMED


def application_read(buffer: ReceiveBuffer, n: int) -> int:
    """The application draining bytes is what reopens the window - never a separate knob."""
    freed = min(n, buffer.buffered)
    buffer.buffered -= freed
    return freed
