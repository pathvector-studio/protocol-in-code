"""Silence means failure.

VRRP backups never ask "are you alive?" - they only listen for the master's
periodic advertisement (see vrrp_election.py for who becomes master). Failover
is not detected as an event; it is INFERRED from the absence of one. A backup
that has heard nothing for long enough concludes, by pure arithmetic on a
clock, that the master is gone.
"""

from __future__ import annotations

from dataclasses import dataclass

ADVERTISEMENT_INTERVAL = 1000
"""Milliseconds between master advertisements (RFC 5798's default Advertisement_Interval)."""


def master_down_interval(priority: int) -> int:
    """How long a backup waits in silence before declaring the master dead.

    RFC 5798: Master_Down_Interval = (3 * Advertisement_Interval) + Skew_Time,
    where Skew_Time = ((256 - priority) * Advertisement_Interval) / 256. The
    skew is the reading target here: a HIGHER priority backup gets a SMALLER
    skew, so among several backups timing out the same silence, the
    best-priority one always declares the master dead first and takes over -
    the skew turns a tie into an ordered race.
    """
    skew = ((256 - priority) * ADVERTISEMENT_INTERVAL) // 256
    return 3 * ADVERTISEMENT_INTERVAL + skew


@dataclass
class BackupWatch:
    last_heard_at: int


def heartbeat(watch: BackupWatch, now: int) -> None:
    """An advertisement arrives: reset the silence clock."""
    watch.last_heard_at = now


def master_is_down(watch: BackupWatch, priority: int, now: int) -> bool:
    """Has this backup's own Master_Down_Interval elapsed since the last advertisement?

    Pure arithmetic on silence: no packet is exchanged to make this
    determination, only a comparison against a clock.
    """
    return now >= watch.last_heard_at + master_down_interval(priority)
