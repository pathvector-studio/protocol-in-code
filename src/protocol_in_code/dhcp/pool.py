from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .offer import OFFER_HOLD_SECONDS

CANDIDATE_START = 10
CANDIDATE_END = 50


class PoolOutcome(str, Enum):
    ASSIGNED = "Assigned"
    POOL_EXHAUSTED = "PoolExhausted"


@dataclass
class AddressPool:
    """The pool hands out what's free: one /24, a visible slice of it up for grabs."""

    network_prefix: str
    allocated: set[str] = field(default_factory=set)
    on_hold: dict[str, int] = field(default_factory=dict)


def _candidates(pool: AddressPool) -> tuple[str, ...]:
    return tuple(f"{pool.network_prefix}.{host}" for host in range(CANDIDATE_START, CANDIDATE_END + 1))


def next_free(pool: AddressPool, now: int) -> str | None:
    """Walk the candidate range in order, skipping anything allocated or still on hold.

    Returns None (POOL_EXHAUSTED) if every candidate address is either allocated to a
    lease or held by an offer whose OFFER_HOLD_SECONDS window hasn't elapsed yet.
    """
    for ip in _candidates(pool):
        if ip in pool.allocated:
            continue
        held_at = pool.on_hold.get(ip)
        if held_at is not None and now < held_at + OFFER_HOLD_SECONDS:
            continue
        return ip
    return None


def hold(pool: AddressPool, ip: str, now: int) -> None:
    """Reserve an address for an outstanding OFFER, timestamped with when the hold began."""
    pool.on_hold[ip] = now


def allocate(pool: AddressPool, ip: str) -> None:
    """Turn a hold (or a bare address) into a real allocation and clear any leftover hold."""
    pool.allocated.add(ip)
    pool.on_hold.pop(ip, None)


def release(pool: AddressPool, ip: str) -> None:
    """Return an address to the free pool - lease ended, released, or the client left."""
    pool.allocated.discard(ip)
    pool.on_hold.pop(ip, None)
