from __future__ import annotations

from dataclasses import dataclass

from .cost import select_best_routes
from .routing import OSPFRoute


@dataclass(frozen=True)
class SummaryLSA:
    prefix: str
    summary_metric: int
    source_area: str
    target_area: str
    abr_router_id: str


def summarize_area_routes(
    routes: tuple[OSPFRoute, ...],
    source_area: str,
    target_area: str,
    abr_router_id: str,
) -> tuple[SummaryLSA, ...]:
    internal = tuple(
        route
        for route in routes
        if route.area_id == source_area and route.route_type == "intra_area"
    )
    best_routes = select_best_routes(internal)
    return tuple(
        SummaryLSA(
            prefix=route.prefix,
            summary_metric=route.total_cost,
            source_area=source_area,
            target_area=target_area,
            abr_router_id=abr_router_id,
        )
        for route in best_routes
    )


def import_summary_lsas(
    area_id: str,
    summaries: tuple[SummaryLSA, ...],
    cost_to_abr: dict[str, int],
) -> tuple[OSPFRoute, ...]:
    return tuple(
        OSPFRoute(
            prefix=summary.prefix,
            next_hop_router_id=summary.abr_router_id,
            total_cost=cost_to_abr[summary.abr_router_id] + summary.summary_metric,
            area_id=area_id,
            route_type="inter_area",
        )
        for summary in summaries
        if summary.target_area == area_id and summary.abr_router_id in cost_to_abr
    )
