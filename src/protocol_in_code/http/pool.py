from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

IDLE_TIMEOUT = 30


class CheckoutOutcome(str, Enum):
    REUSED = "Reused"
    NEW = "New"


@dataclass(frozen=True)
class IdleConnection:
    conn_id: int
    idle_since: int


@dataclass
class ConnectionPool:
    """Keep-alive is a pool: idle connections wait per host, ready to be reused."""

    idle: dict[str, list[IdleConnection]] = field(default_factory=dict)
    next_conn_id: int = 1


@dataclass(frozen=True)
class CheckoutResult:
    outcome: CheckoutOutcome
    conn_id: int


def _evict_expired(pool: ConnectionPool, host: str, now: int) -> None:
    connections = pool.idle.get(host, [])
    pool.idle[host] = [c for c in connections if now - c.idle_since < IDLE_TIMEOUT]


def checkout(pool: ConnectionPool, host: str, now: int) -> CheckoutResult:
    """Ask the pool for a connection: reuse a fresh idle one, or mint a new one."""
    _evict_expired(pool, host, now)

    connections = pool.idle.get(host, [])
    if connections:
        reused = connections.pop()
        return CheckoutResult(CheckoutOutcome.REUSED, reused.conn_id)

    conn_id = pool.next_conn_id
    pool.next_conn_id += 1
    return CheckoutResult(CheckoutOutcome.NEW, conn_id)


def checkin(pool: ConnectionPool, host: str, conn_id: int, now: int) -> None:
    """Return a connection to the pool, idle as of now, available for the next checkout."""
    pool.idle.setdefault(host, []).append(IdleConnection(conn_id, now))


if __name__ == "__main__":
    pool = ConnectionPool()

    first = checkout(pool, "example.com", now=0)
    assert first.outcome is CheckoutOutcome.NEW
    checkin(pool, "example.com", first.conn_id, now=0)

    reused = checkout(pool, "example.com", now=10)
    assert reused.outcome is CheckoutOutcome.REUSED
    assert reused.conn_id == first.conn_id
    checkin(pool, "example.com", reused.conn_id, now=10)

    # Idle since 10; eviction condition is "now - idle_since < IDLE_TIMEOUT".
    # At now=40, 40 - 10 == IDLE_TIMEOUT exactly, so the connection is evicted (not "<").
    at_boundary = checkout(pool, "example.com", now=10 + IDLE_TIMEOUT)
    assert at_boundary.outcome is CheckoutOutcome.NEW

    print("[OK] pool.py")
