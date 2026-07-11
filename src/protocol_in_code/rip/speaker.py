"""Build the toy RIP loop.

A ToyRipSpeaker owns a routing table, a set of directly connected prefixes,
and a list of neighbors. Each round it advertises to every neighbor
(filtered through split_horizon.py) and receives whatever its neighbors
sent last round (folded in through update.py's Bellman-Ford pass).
converge() round-robins this exchange until no speaker's table changes, or
a round limit is hit, and reports how many rounds it took.

The contrast with ospf/speaker.py is the thesis of this whole track: OSPF
floods facts unchanged and each router recomputes shortest paths locally
from a shared map (see ospf/spf.py's Dijkstra run over a graph everyone
agrees on). RIP never builds a map. It passes distance rumors hop by hop
and trusts arithmetic — "believe your neighbor, add one" — to eventually
settle. Same problem, reachability and cost, solved by opposite philosophies:
one router computing over shared truth, versus many routers gossiping over
partial truth until it stabilizes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .infinity import poison
from .route import RipRoute
from .split_horizon import advertisable
from .update import RoutingTable, UpdateOutcome, process_advertisement


@dataclass
class ToyRipSpeaker:
    name: str
    table: RoutingTable = field(default_factory=RoutingTable)
    connected: dict[str, int] = field(default_factory=dict)
    neighbors: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        for prefix, metric in self.connected.items():
            self.table.routes[prefix] = RipRoute(
                prefix=prefix,
                metric=metric,
                next_hop=self.name,
                learned_from=self.name,
            )

    def advertise_to(self, neighbor: str) -> tuple[tuple[str, int], ...]:
        """Outbound: filtered through split horizon so we never echo a rumor back to its source."""
        return advertisable(self.table, to_neighbor=neighbor)

    def receive(self, neighbor: str, advertised: tuple[tuple[str, int], ...]) -> tuple[UpdateOutcome, ...]:
        """Inbound: fold a neighbor's advertisement into our table via Bellman-Ford."""
        outcomes = process_advertisement(self.table, neighbor=neighbor, advertised=advertised)
        for (prefix, _metric), outcome in zip(advertised, outcomes):
            self.trace.append(f"{self.name}: from {neighbor}, {prefix} -> {outcome.value}")
        return outcomes

    def lose_connected(self, prefix: str) -> None:
        """A directly attached link goes down: poison the route rather than deleting it silently."""
        current = self.table.routes.get(prefix)
        if current is None:
            return
        self.table.routes[prefix] = poison(current)
        self.connected.pop(prefix, None)
        self.trace.append(f"{self.name}: lost connected {prefix}, poisoned")


@dataclass(frozen=True)
class ConvergenceReport:
    rounds_run: int
    converged: bool
    final_tables: dict[str, dict[str, int]]


def converge(speakers: dict[str, ToyRipSpeaker], rounds: int) -> ConvergenceReport:
    """Round-robin every speaker's advertisement to every neighbor until no table changes."""
    for round_no in range(1, rounds + 1):
        outgoing: dict[tuple[str, str], tuple[tuple[str, int], ...]] = {}
        for name, speaker in speakers.items():
            for neighbor in speaker.neighbors:
                outgoing[(name, neighbor)] = speaker.advertise_to(neighbor)

        changed = False
        for (sender, receiver), advertised in outgoing.items():
            if receiver not in speakers:
                continue
            before = dict(speakers[receiver].table.routes)
            speakers[receiver].receive(sender, advertised)
            if speakers[receiver].table.routes != before:
                changed = True

        if not changed:
            return ConvergenceReport(
                rounds_run=round_no,
                converged=True,
                final_tables=_snapshot(speakers),
            )

    return ConvergenceReport(
        rounds_run=rounds,
        converged=False,
        final_tables=_snapshot(speakers),
    )


def _snapshot(speakers: dict[str, ToyRipSpeaker]) -> dict[str, dict[str, int]]:
    return {
        name: {prefix: route.metric for prefix, route in sorted(speaker.table.routes.items())}
        for name, speaker in speakers.items()
    }
