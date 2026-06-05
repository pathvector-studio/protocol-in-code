from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .routing import OSPFRoute


@dataclass(frozen=True)
class RouteDecision:
    prefix: str
    winner: OSPFRoute
    compared: tuple[OSPFRoute, ...]


def _route_type_rank(route_type: str) -> int:
    return 0 if route_type == "intra_area" else 1


def select_best_route(candidates: tuple[OSPFRoute, ...]) -> RouteDecision | None:
    if not candidates:
        return None

    winner = min(
        candidates,
        key=lambda route: (
            _route_type_rank(route.route_type),
            route.total_cost,
            route.area_id,
            route.next_hop_router_id,
        ),
    )
    return RouteDecision(prefix=winner.prefix, winner=winner, compared=candidates)


def select_best_routes(routes: tuple[OSPFRoute, ...]) -> tuple[OSPFRoute, ...]:
    grouped: dict[str, list[OSPFRoute]] = defaultdict(list)
    for route in routes:
        grouped[route.prefix].append(route)

    winners: list[OSPFRoute] = []
    for prefix, candidates in grouped.items():
        decision = select_best_route(tuple(candidates))
        if decision is not None:
            winners.append(decision.winner)

    return tuple(
        sorted(
            winners,
            key=lambda route: (
                route.prefix,
                _route_type_rank(route.route_type),
                route.total_cost,
                route.next_hop_router_id,
                route.area_id,
            ),
        )
    )
