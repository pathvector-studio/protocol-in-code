from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# One public IP can carry roughly 16k concurrent flows per protocol per
# destination - the ephemeral port range IS the NAT's capacity. Every
# outbound flow through this IP consumes one port from this pool until its
# entry expires (see timeout.py); run the pool dry and new connections stall.
EPHEMERAL_RANGE = (49152, 65535)


class AllocationOutcome(str, Enum):
    ALLOCATED = "Allocated"
    POOL_EXHAUSTED = "PoolExhausted"


@dataclass
class PortAllocator:
    """The shared pool for one public IP: which ports are taken, and where to resume scanning."""

    public_ip: str
    in_use: set[int] = field(default_factory=set)
    next_candidate: int = EPHEMERAL_RANGE[0]


def allocate_port(alloc: PortAllocator) -> int | None:
    """Scan from next_candidate for a free port, wrapping once; None means the pool is exhausted."""
    low, high = EPHEMERAL_RANGE
    span = high - low + 1

    for offset in range(span):
        candidate = low + (alloc.next_candidate - low + offset) % span
        if candidate not in alloc.in_use:
            alloc.in_use.add(candidate)
            alloc.next_candidate = candidate + 1 if candidate < high else low
            return candidate

    return None


def release_port(alloc: PortAllocator, port: int) -> None:
    """Give a port back to the pool - the mirror image of allocate_port, called on entry expiry."""
    alloc.in_use.discard(port)
