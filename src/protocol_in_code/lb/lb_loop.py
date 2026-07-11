"""Build the toy load balancer loop.

Every earlier file in this track answers one question in isolation: how do
you pick among backends assumed to all be up (round_robin.py, least_conn.py,
hash_pick.py, ring.py), and how do you know which ones actually are
(health.py). `ToyLoadBalancer` is where those questions meet a live request:
filter the backend list down to what's eligible right now, then hand the
survivors to whichever picking strategy is configured. Nothing here
invents new theory — it wires together five files that already did the
thinking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .hash_pick import pick as hash_pick
from .health import BackendHealth, HealthState, eligible, record_probe
from .least_conn import ConnCounts
from .least_conn import connection_closed as lc_connection_closed
from .least_conn import connection_opened as lc_connection_opened
from .least_conn import pick as lc_pick
from .ring import build_ring
from .ring import pick as ring_pick
from .round_robin import RoundRobinState
from .round_robin import pick as rr_pick


class Strategy(str, Enum):
    ROUND_ROBIN = "Round robin"
    LEAST_CONN = "Least connections"
    RING = "Ring"


@dataclass
class ToyLoadBalancer:
    """The smallest integration demo: filter by health, then delegate to one strategy."""

    backends: tuple[str, ...]
    strategy: Strategy = Strategy.ROUND_ROBIN
    vnodes_per_backend: int = 100
    clock: int = 0
    round_robin_state: RoundRobinState = field(init=False)
    conn_counts: ConnCounts = field(default_factory=ConnCounts)
    health: dict[str, HealthState] = field(init=False)
    trace: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.round_robin_state = RoundRobinState(backends=self.backends)
        self.health = {backend: HealthState() for backend in self.backends}

    def tick(self, seconds: int) -> None:
        self.clock += seconds

    def _eligible_backends(self) -> tuple[str, ...]:
        return tuple(
            backend for backend in self.backends if eligible(self.health[backend].status)
        )

    def route(self, client_key: str) -> str | None:
        """Filter to eligible backends, then delegate to the configured strategy.

        RING rebuilds its ring over only the currently-eligible backends on
        every call. That is not free — building the ring is
        O(vnodes_per_backend * len(backends)) — but the toy favors an
        honest, obviously-correct rebuild over a production-grade
        incremental ring update. A real load balancer would rebuild the
        ring only when membership actually changes, not on every request.
        """
        candidates = self._eligible_backends()
        if not candidates:
            self.trace.append(f"route {client_key}: no eligible backends")
            return None

        if self.strategy is Strategy.ROUND_ROBIN:
            live_state = RoundRobinState(backends=candidates, next_index=self.round_robin_state.next_index)
            backend = rr_pick(live_state)
            self.round_robin_state.next_index = live_state.next_index
        elif self.strategy is Strategy.LEAST_CONN:
            backend = lc_pick(self.conn_counts, candidates)
        else:
            ring = build_ring(candidates, self.vnodes_per_backend)
            backend = ring_pick(ring, client_key)

        self.trace.append(f"route {client_key}: {self.strategy.value} -> {backend}")
        return backend

    def connection_opened(self, backend: str) -> None:
        lc_connection_opened(self.conn_counts, backend)

    def connection_closed(self, backend: str) -> None:
        lc_connection_closed(self.conn_counts, backend)

    def probe_result(self, backend: str, ok: bool) -> BackendHealth:
        """Feed one probe result into `backend`'s health state and trace the outcome."""
        status = record_probe(self.health[backend], ok)
        self.trace.append(f"probe {backend}: {'ok' if ok else 'fail'} -> {status.value}")
        return status


def run_scenario(lb: ToyLoadBalancer, requests: tuple[tuple[str, tuple[str, bool] | None], ...]) -> None:
    """Drive the toy load balancer through a scripted scenario, tracing every decision.

    Each entry in `requests` is (client_key, probe_or_none). When the
    second element is a (backend, ok) pair, a health probe fires before the
    route decision — this is how the scenario stages "a backend goes DOWN
    mid-stream." With RING as the strategy, the same client_key keeps
    hitting the same backend across calls until that backend's health takes
    it out of the eligible set; every other strategy has no such memory and
    can move a key at any tick.
    """
    for client_key, probe in requests:
        if probe is not None:
            backend, ok = probe
            lb.probe_result(backend, ok)

        chosen = lb.route(client_key)
        if chosen is not None:
            lb.connection_opened(chosen)
