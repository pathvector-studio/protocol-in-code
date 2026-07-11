from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .five_tuple import FiveTuple, reply_tuple


class MatchDirection(str, Enum):
    FORWARD = "Forward"
    REVERSE = "Reverse"
    NO_MATCH = "NoMatch"


@dataclass(frozen=True)
class NatEntry:
    """One translation, remembered: the tuple as the private host sent it, and the tuple as the world sees it."""

    original: FiveTuple
    translated: FiveTuple
    created_at: int


@dataclass
class ConntrackTable:
    entries: dict[FiveTuple, NatEntry] = field(default_factory=dict)


@dataclass(frozen=True)
class MatchResult:
    direction: MatchDirection
    entry: NatEntry | None


def insert(table: ConntrackTable, entry: NatEntry) -> None:
    """The reply finds its way back because it was pre-computed here, not figured out when it arrives.

    On outbound SNAT the table gets TWO keys for one entry: the original tuple, so a
    retransmit from the same private host matches forward, and the reply direction of
    the translated tuple, so the very first packet coming back from the internet already
    has a home. Nothing "learns" the return path later - it exists before the first
    outbound packet even leaves.
    """
    table.entries[entry.original] = entry
    table.entries[reply_tuple(entry.translated)] = entry


def match(table: ConntrackTable, packet_tuple: FiveTuple) -> MatchResult:
    """Classify an incoming tuple against the table: same-direction repeat, reply, or nothing we started."""
    entry = table.entries.get(packet_tuple)
    if entry is None:
        return MatchResult(MatchDirection.NO_MATCH, None)

    if packet_tuple == entry.original:
        return MatchResult(MatchDirection.FORWARD, entry)

    return MatchResult(MatchDirection.REVERSE, entry)


def remove(table: ConntrackTable, entry: NatEntry) -> None:
    """Undo both inserts at once - a mapping is created as a pair and it expires as a pair."""
    table.entries.pop(entry.original, None)
    table.entries.pop(reply_tuple(entry.translated), None)
