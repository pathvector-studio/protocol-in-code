from __future__ import annotations

from .five_tuple import reply_tuple
from .table import ConntrackTable, NatEntry

# State expires, again. This is the fourth appearance of the expiring-dict shape
# in this course: src/protocol_in_code/dns/cache.py (records expire by TTL),
# src/protocol_in_code/tls/resumption.py (tickets expire by lifetime), and (if
# generated) src/protocol_in_code/dhcp/leases.py (leases expire and must be
# renewed) all store a value stamped with the time it was created and check
# age against a limit at read time. NAT conntrack entries are the same idea -
# but here expiry has a consequence nobody asked for: an idle UDP mapping
# dying is "hole punching" in reverse. Neither endpoint closed anything, no
# FIN or RST was ever sent, yet the next packet from the far side arrives to
# find NO_MATCH and gets silently dropped. The flow is dead and both sides
# have to find out the hard way.

# Real conntrack timeouts are wildly asymmetric: TCP has an explicit close
# (FIN/RST) so idle established connections can be trusted for a long time,
# while UDP has no close signal at all, so the table has to guess a flow is
# over just because it went quiet.
EXPIRY_SECONDS = {
    "tcp": 300,
    "udp": 30,
}


def is_expired(entry: NatEntry, now: int) -> bool:
    limit = EXPIRY_SECONDS.get(entry.original.protocol, EXPIRY_SECONDS["tcp"])
    return now >= entry.created_at + limit


def touch(entry: NatEntry, now: int) -> NatEntry:
    """Traffic refreshes an entry: frozen in, frozen out, so the caller re-inserts the new one."""
    return NatEntry(
        original=entry.original,
        translated=entry.translated,
        created_at=now,
    )


def sweep(table: ConntrackTable, now: int) -> tuple:
    """Remove every entry whose protocol timeout has passed, both keys at once, and report what died."""
    expired = {
        entry
        for entry in table.entries.values()
        if is_expired(entry, now)
    }

    removed = []
    for entry in expired:
        table.entries.pop(entry.original, None)
        table.entries.pop(reply_tuple(entry.translated), None)
        removed.append(entry.original)

    return tuple(removed)
