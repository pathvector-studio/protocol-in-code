from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# Contrast with dns/cache.py: that resolver cache's entries expire to ABSENCE —
# entry_is_expired() deletes the key and the next lookup is a plain MISS. This
# neighbor cache's entries expire to a WEAKER STATE instead. A REACHABLE mapping
# that outlives REACHABLE_SECONDS does not vanish; it degrades to STALE, which is
# still usable for forwarding but flags itself for re-confirmation. That's the
# shape of IPv6 Neighbor Discovery's neighbor cache state machine (loosely, RFC
# 4861 §7.3): REACHABLE -> STALE is a mood swing, not a deletion. A cache with
# moods, not just a deadline.

REACHABLE_SECONDS = 30


class NeighborState(str, Enum):
    INCOMPLETE = "Incomplete"
    REACHABLE = "Reachable"
    STALE = "Stale"


@dataclass
class NeighborEntry:
    mac: str | None
    state: NeighborState
    updated_at: int


@dataclass
class NeighborCache:
    entries: dict[str, NeighborEntry] = field(default_factory=dict)


@dataclass(frozen=True)
class LookupResult:
    state: NeighborState | None
    mac: str | None


def lookup(cache: NeighborCache, ip: str, now: int) -> LookupResult:
    """Ask the cache for a mapping; a REACHABLE entry past its time degrades to STALE in place."""
    entry = cache.entries.get(ip)
    if entry is None:
        return LookupResult(None, None)

    if entry.state is NeighborState.REACHABLE and now - entry.updated_at >= REACHABLE_SECONDS:
        entry.state = NeighborState.STALE

    return LookupResult(entry.state, entry.mac)


def start_resolution(cache: NeighborCache, ip: str, now: int) -> None:
    """A who-has goes out; until the reply arrives the entry holds no MAC at all."""
    cache.entries[ip] = NeighborEntry(mac=None, state=NeighborState.INCOMPLETE, updated_at=now)


def confirm(cache: NeighborCache, ip: str, mac: str, now: int) -> None:
    """A reply (solicited or gleaned) lands: the entry is REACHABLE again, freshly timestamped."""
    cache.entries[ip] = NeighborEntry(mac=mac, state=NeighborState.REACHABLE, updated_at=now)
