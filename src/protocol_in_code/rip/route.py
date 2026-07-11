"""A route is a rumor with a distance.

An OSPF Router-LSA (see ospf/lsa.py) is a fact about topology: a router
describes its own links, and every other router floods that fact unchanged
across the area. RIP has no such fact. A RipRoute is hearsay — "my neighbor
says this prefix is `metric` hops away" — and the metric already bakes in
the neighbor's own uncertainty plus the one hop it took to reach us. There
is no shared map to recompute from, only a number to trust or not.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class RipRoute:
    prefix: str
    metric: int
    next_hop: str
    learned_from: str


class RouteValidity(str, Enum):
    VALID = "Valid"
    NEGATIVE_METRIC = "Negative metric"
    METRIC_TOO_HIGH = "Metric exceeds infinity"


def validate_route(route: RipRoute) -> RouteValidity:
    """A metric is a hop count, not a signed quantity, and RIP bounds it at 16 (see infinity.py)."""
    if route.metric < 0:
        return RouteValidity.NEGATIVE_METRIC
    if route.metric > 16:
        return RouteValidity.METRIC_TOO_HIGH
    return RouteValidity.VALID


def better(a: RipRoute, b: RipRoute) -> bool:
    """Is `a` preferable to `b`? Lower metric wins.

    Third appearance of selection-by-comparison in this course: OSPF picks a
    winner by total_cost in ospf/cost.py, BGP picks a winner by a multi-step
    attribute chain in bgp/best_path.py, and RIP picks a winner by a single
    integer. Same shape, thinner rulebook.
    """
    return a.metric < b.metric
