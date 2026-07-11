"""Sixteen means unreachable.

RIP needs a metric value that means "not reachable at all," so it can be
carried in the same integer field as every other distance. It picks 16, not
a billion. That choice looks stingy until you meet count_to_infinity.py:
when a rumor loops between two routers, each exchange adds one hop, and the
metric climbs until it crosses this ceiling. A small ceiling means the
pathology tops out in a handful of rounds instead of grinding toward a
huge number forever. Sixteen is not a limit on network size so much as a
deliberately short fuse on how long a bad rumor can circulate.
"""

from __future__ import annotations

from dataclasses import replace

from .route import RipRoute

INFINITY = 16


def is_unreachable(metric: int) -> bool:
    return metric >= INFINITY


def clamp_metric(metric: int) -> int:
    """Advertised distances never exceed INFINITY; arithmetic that overshoots gets capped."""
    return min(metric, INFINITY)


def poison(route: RipRoute) -> RipRoute:
    """Route poisoning: declare a route dead on purpose by setting its metric to INFINITY."""
    return replace(route, metric=INFINITY)
