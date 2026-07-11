"""Rumors can circle back.

Two routers, A and B, both know a prefix. A has it directly; B only knows
it through A. A loses the direct route. If A and B naively keep exchanging
full advertisements, B still tells A "I can reach it, metric X" — because B
never checks whether the reachability it is offering originally came from A
in the first place. A believes B (a neighbor is a neighbor), adopts
metric X + 1, and now advertises that back to B. B adopts *that* + 1. Each
round both metrics climb by one until they cross INFINITY (see infinity.py)
and the route is finally, correctly, declared dead. This module simulates
the climb, and then simulates the fix.

Import direction: this file imports advertisable() from split_horizon.py.
split_horizon.py has no dependency on this file. That is deliberate —
split horizon is the general-purpose filter (used any time a router speaks),
and this module is one demonstration consuming it, not the other way
around. The alternative (inlining suppression here and pointing forward)
would tie the fix to a single demo instead of a reusable rule; the whole
point of session order is that the cure is introduced as its own filter.
"""

from __future__ import annotations

from dataclasses import dataclass

from .infinity import INFINITY
from .route import RipRoute
from .split_horizon import advertisable
from .update import RoutingTable, process_advertisement

PREFIX = "10.0.0.0/24"


@dataclass(frozen=True)
class RoundSnapshot:
    round_no: int
    a_metric: int
    b_metric: int


@dataclass(frozen=True)
class CountResult:
    rounds: tuple[RoundSnapshot, ...]
    converged_at: int | None


def simulate_count_to_infinity(max_rounds: int) -> CountResult:
    """No split horizon: A and B trade the same rumor back and forth, each hop adding one,
    until both sides hit INFINITY and the route is finally retired.
    """
    # Starting point: A directly connects the prefix (metric 1), B learned it through A (metric 2).
    # Then A's direct connection dies — A no longer has a route of its own.
    table_a = RoutingTable()
    table_b = RoutingTable(routes={PREFIX: RipRoute(PREFIX, metric=2, next_hop="A", learned_from="A")})

    rounds: list[RoundSnapshot] = []
    converged_at: int | None = None

    for round_no in range(1, max_rounds + 1):
        # B tells A what it knows (no filtering); A adopts/updates via the same-source rule.
        b_advertised = tuple((prefix, route.metric) for prefix, route in sorted(table_b.routes.items()))
        process_advertisement(table_a, neighbor="B", advertised=b_advertised)

        # A tells B what it knows in turn.
        a_advertised = tuple((prefix, route.metric) for prefix, route in sorted(table_a.routes.items()))
        process_advertisement(table_b, neighbor="A", advertised=a_advertised)

        a_metric = table_a.routes[PREFIX].metric
        b_metric = table_b.routes[PREFIX].metric
        rounds.append(RoundSnapshot(round_no=round_no, a_metric=a_metric, b_metric=b_metric))

        if a_metric >= INFINITY and b_metric >= INFINITY and converged_at is None:
            converged_at = round_no
            break

    return CountResult(rounds=tuple(rounds), converged_at=converged_at)


def simulate_with_split_horizon(max_rounds: int) -> CountResult:
    """Same starting state, same exchange loop — but each side filters what it sends
    through advertisable(), so the rumor can't bounce back to its source.
    """
    table_a = RoutingTable()
    table_b = RoutingTable(routes={PREFIX: RipRoute(PREFIX, metric=2, next_hop="A", learned_from="A")})

    rounds: list[RoundSnapshot] = []
    converged_at: int | None = None

    for round_no in range(1, max_rounds + 1):
        b_advertised = advertisable(table_b, to_neighbor="A")
        process_advertisement(table_a, neighbor="B", advertised=b_advertised)

        a_advertised = advertisable(table_a, to_neighbor="B")
        process_advertisement(table_b, neighbor="A", advertised=a_advertised)

        a_route = table_a.routes.get(PREFIX)
        b_route = table_b.routes.get(PREFIX)
        a_metric = a_route.metric if a_route is not None else INFINITY
        b_metric = b_route.metric if b_route is not None else INFINITY
        rounds.append(RoundSnapshot(round_no=round_no, a_metric=a_metric, b_metric=b_metric))

        if a_metric >= INFINITY and converged_at is None:
            converged_at = round_no
            break

    return CountResult(rounds=tuple(rounds), converged_at=converged_at)
