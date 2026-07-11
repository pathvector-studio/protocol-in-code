"""Least connections is a counter.

Round robin (round_robin.py) needed no memory of the backends themselves —
just a position. Least connections needs exactly one integer per backend:
how many requests are in flight there right now. That counter is the state
round robin got to skip, and it is also the entire feature — everything
below exists to keep the counters honest as connections open and close.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ConnCounts:
    active: dict[str, int] = field(default_factory=dict)


def pick(counts: ConnCounts, backends: tuple[str, ...]) -> str:
    """Pick the backend with the fewest active connections.

    Ties are broken by backend name, ascending. Without a tiebreak, `min()`
    would silently favor whichever backend happens to appear first in
    `backends`, which makes the choice depend on iteration order instead of
    on anything meaningful — deterministic-but-arbitrary is worse than
    deterministic-and-documented.
    """
    if not backends:
        raise ValueError("no backends to pick from")

    return min(backends, key=lambda backend: (counts.active.get(backend, 0), backend))


def connection_opened(counts: ConnCounts, backend: str) -> None:
    """A request was routed to `backend`; its counter goes up."""
    counts.active[backend] = counts.active.get(backend, 0) + 1


def connection_closed(counts: ConnCounts, backend: str) -> None:
    """A request finished on `backend`; its counter comes back down, floored at zero.

    The floor matters: without it, a `connection_closed` call that outlives
    the counts we tracked (e.g. after a restart wiped `active`) could drive
    a count negative and make that backend look artificially attractive to
    `pick` forever after.
    """
    current = counts.active.get(backend, 0)
    counts.active[backend] = max(0, current - 1)
