"""Round robin is one index.

There is no health data, no load data, no history — just a pointer into a
tuple that moves forward and wraps. That poverty is the point: round robin
is the load balancer you reach for when you have decided you don't need to
know anything about the backends to spread work across them evenly. Every
other strategy in this track (least_conn.py, hash_pick.py, ring.py) adds
state because round robin's blindness eventually costs something.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RoundRobinState:
    backends: tuple[str, ...]
    next_index: int = 0


def pick(state: RoundRobinState) -> str:
    """Hand out backends[next_index], then advance the index with modulo.

    The entire algorithm is one integer that walks a ring of array
    positions. No comparison, no memory of who was picked last time beyond
    this single field.
    """
    if not state.backends:
        raise ValueError("no backends to pick from")

    backend = state.backends[state.next_index % len(state.backends)]
    state.next_index = (state.next_index + 1) % len(state.backends)
    return backend


def pick_weighted(state: RoundRobinState, weights: dict[str, int]) -> str:
    """Weighted round robin, done the dumbest honest way: expand the list.

    A backend with weight 2 is simply listed twice before the index walks
    it. This is not the smooth interleaving a production load balancer
    would use (which staggers repeats so one backend doesn't get two
    requests back-to-back) — it is the expanded-list approach, and it earns
    its keep by being obvious: read `expanded` and you can see the exact
    proportions before a single request is routed. Missing weights default
    to 1.
    """
    if not state.backends:
        raise ValueError("no backends to pick from")

    expanded = tuple(
        backend for backend in state.backends for _ in range(max(1, weights.get(backend, 1)))
    )

    backend = expanded[state.next_index % len(expanded)]
    state.next_index = (state.next_index + 1) % len(expanded)
    return backend
