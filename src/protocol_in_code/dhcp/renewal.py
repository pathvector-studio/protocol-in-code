from __future__ import annotations

from enum import Enum

from .leases import Lease

# RFC 2131 section 4.4.5 defaults: renewal (T1) at 50% of the lease and
# rebinding (T2) at 87.5% of the lease. Both are computed with integer
# arithmetic and both round down, so a lease can end up very slightly
# short-changed rather than ever granted extra time.


class RenewalState(str, Enum):
    FRESH = "Fresh"
    RENEWING = "Renewing"
    REBINDING = "Rebinding"
    EXPIRED = "Expired"


def t1(lease: Lease) -> int:
    """T1: renewal begins at half the lease - integer division, rounds down."""
    return lease.granted_at + lease.duration // 2


def t2(lease: Lease) -> int:
    """T2: rebinding begins at seven-eighths of the lease - same rounding rule as T1."""
    return lease.granted_at + lease.duration * 7 // 8


def renewal_state(lease: Lease, now: int) -> RenewalState:
    """Renewal happens before the end: a lease passes through three deadlines, not one.

    Before T1 the lease is FRESH and nobody needs to do anything. From T1 up to (but
    not including) T2 the client is RENEWING - it asks quietly, unicast, the server
    that granted it. From T2 up to (but not including) expiry the client is REBINDING -
    louder now, broadcast, because the granting server might be gone and any server on
    the segment who recognizes this lease can answer. At or past expiry the lease is
    just EXPIRED.
    """
    expiry = lease.granted_at + lease.duration
    if now >= expiry:
        return RenewalState.EXPIRED
    if now >= t2(lease):
        return RenewalState.REBINDING
    if now >= t1(lease):
        return RenewalState.RENEWING
    return RenewalState.FRESH


def renewal_target(state: RenewalState) -> str:
    """The who-do-you-ask table: each renewal state has exactly one kind of answer."""
    if state is RenewalState.RENEWING:
        return "granting-server"
    if state is RenewalState.REBINDING:
        return "any-server"
    return "none"
