from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# A lease is a dict with an expiry - the same shape as every other cache in this
# course: src/protocol_in_code/dns/cache.py (records expire by TTL),
# src/protocol_in_code/tls/resumption.py (tickets expire by lifetime), and
# src/protocol_in_code/nat/timeout.py (conntrack entries expire by idle timeout)
# all store a value stamped with the time it was created and check its age
# against a limit at read time, deleting it on the way out if it's too old.
# This is the expiring-dict shape's fourth and last appearance in the course.
# By now you should recognize it on sight: a dict keyed by identity, a frozen
# value carrying its own birth time, and a lookup function that is also the
# only place expiry is ever checked.


class LeaseOutcome(str, Enum):
    HIT = "Hit"
    MISS = "Miss"
    EXPIRED = "Expired"


@dataclass(frozen=True)
class Lease:
    ip: str
    granted_at: int
    duration: int


@dataclass
class LeaseTable:
    leases: dict[str, Lease] = field(default_factory=dict)


@dataclass(frozen=True)
class LeaseLookup:
    outcome: LeaseOutcome
    lease: Lease | None


def lease_is_expired(lease: Lease, now: int) -> bool:
    return now >= lease.granted_at + lease.duration


def lookup_lease(table: LeaseTable, mac: str, now: int) -> LeaseLookup:
    """A lease is good until it isn't: expiry is discovered here, at read time, not on a timer."""
    lease = table.leases.get(mac)
    if lease is None:
        return LeaseLookup(LeaseOutcome.MISS, None)

    if lease_is_expired(lease, now):
        del table.leases[mac]
        return LeaseLookup(LeaseOutcome.EXPIRED, None)

    return LeaseLookup(LeaseOutcome.HIT, lease)


def grant_lease(table: LeaseTable, mac: str, ip: str, duration: int, now: int) -> Lease:
    """An ACK earns the client a lease, stamped with the moment the server granted it."""
    lease = Lease(ip=ip, granted_at=now, duration=duration)
    table.leases[mac] = lease
    return lease
