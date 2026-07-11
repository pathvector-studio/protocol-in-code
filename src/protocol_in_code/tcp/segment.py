from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

FLAG_NAMES = frozenset({"SYN", "ACK", "FIN", "RST"})


class SegmentValidity(str, Enum):
    BAD_FLAG_NAME = "BadFlagName"
    SYN_FIN_TOGETHER = "SynFinTogether"
    PAYLOAD_WITHOUT_SEQ_MEANING = "PayloadWithoutSeqMeaning"
    NEGATIVE_LENGTH = "NegativeLength"
    VALID = "Valid"


@dataclass(frozen=True)
class Segment:
    """A segment carries the conversation state: who is talking, and what they've heard."""

    seq: int
    ack: int
    flags: frozenset[str] = field(default_factory=frozenset)
    payload_len: int = 0
    window: int = 0


def is_syn(segment: Segment) -> bool:
    return "SYN" in segment.flags


def is_ack(segment: Segment) -> bool:
    return "ACK" in segment.flags


def is_fin(segment: Segment) -> bool:
    return "FIN" in segment.flags


def is_rst(segment: Segment) -> bool:
    return "RST" in segment.flags


def flags_label(segment: Segment) -> str:
    """A human-readable rendering like 'SYN,ACK', in the conventional wire order."""
    order = ("SYN", "ACK", "FIN", "RST")
    present = [name for name in order if name in segment.flags]
    return ",".join(present) if present else "(none)"


def validate_segment(segment: Segment) -> SegmentValidity:
    """A segment's flags and payload must agree about what it means before anyone acts on it."""
    if not segment.flags <= FLAG_NAMES:
        return SegmentValidity.BAD_FLAG_NAME
    if is_syn(segment) and is_fin(segment):
        return SegmentValidity.SYN_FIN_TOGETHER
    if segment.payload_len < 0:
        return SegmentValidity.NEGATIVE_LENGTH
    if segment.payload_len > 0 and is_rst(segment):
        # A reset carries no data of its own; a payload on an RST has no seq meaning.
        return SegmentValidity.PAYLOAD_WITHOUT_SEQ_MEANING
    return SegmentValidity.VALID
