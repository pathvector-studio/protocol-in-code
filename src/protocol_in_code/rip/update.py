"""Bellman-Ford is a for loop.

There is no graph object here, no priority queue like ospf/spf.py's Dijkstra
run. A RIP router only ever sees what one neighbor just told it: a list of
(prefix, metric) pairs. Processing an advertisement is a single pass over
that list, relaxing each edge in place. RFC 2453 §3.9.2 describes exactly
this: add one to the advertised metric, and only replace what you already
have if the new number wins or the news came from the same source you were
already trusting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .infinity import clamp_metric
from .route import RipRoute, better


class UpdateOutcome(str, Enum):
    ADOPTED_NEW = "Adopted new route"
    ADOPTED_BETTER = "Adopted better route"
    UPDATED_SAME_SOURCE = "Updated same-source route"
    IGNORED_WORSE = "Ignored worse route"


@dataclass
class RoutingTable:
    routes: dict[str, RipRoute] = field(default_factory=dict)


def process_advertisement(
    table: RoutingTable,
    neighbor: str,
    advertised: tuple[tuple[str, int], ...],
) -> tuple[UpdateOutcome, ...]:
    """RFC 2453 §3.9.2: for each advertised (prefix, metric), the receiving router adds
    the cost of reaching the neighbor (here, a flat 1) before comparing it to what it
    already has.
    """
    outcomes: list[UpdateOutcome] = []

    for prefix, advertised_metric in advertised:
        candidate_metric = clamp_metric(advertised_metric + 1)
        candidate = RipRoute(
            prefix=prefix,
            metric=candidate_metric,
            next_hop=neighbor,
            learned_from=neighbor,
        )

        current = table.routes.get(prefix)
        if current is None:
            table.routes[prefix] = candidate
            outcomes.append(UpdateOutcome.ADOPTED_NEW)
            continue

        if better(candidate, current):
            table.routes[prefix] = candidate
            outcomes.append(UpdateOutcome.ADOPTED_BETTER)
            continue

        if current.learned_from == neighbor:
            # Same-neighbor-overwrite rule: the metric got worse, but this is still
            # our source of truth for the prefix, so we must believe it anyway.
            table.routes[prefix] = candidate
            outcomes.append(UpdateOutcome.UPDATED_SAME_SOURCE)
            continue

        outcomes.append(UpdateOutcome.IGNORED_WORSE)

    return tuple(outcomes)
