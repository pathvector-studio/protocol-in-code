from __future__ import annotations

from dataclasses import dataclass

from .lsa import RouterLSA
from .spf import SPFTree


@dataclass(frozen=True)
class OSPFRoute:
    prefix: str
    next_hop_router_id: str
    total_cost: int
    area_id: str
    route_type: str = "intra_area"


def _first_hop(tree: SPFTree, target_router_id: str) -> str:
    parent = tree.parents.get(target_router_id)
    if parent is None or parent == tree.root_router_id:
        return target_router_id

    current = parent
    while True:
        ancestor = tree.parents.get(current)
        if ancestor is None or ancestor == tree.root_router_id:
            return current
        current = ancestor


def routes_from_tree(
    root_router_id: str,
    tree: SPFTree,
    lsas: tuple[RouterLSA, ...],
) -> tuple[OSPFRoute, ...]:
    routes: list[OSPFRoute] = []

    for lsa in lsas:
        advertising_router = lsa.header.advertising_router
        if advertising_router not in tree.costs:
            continue
        next_hop = root_router_id if advertising_router == root_router_id else _first_hop(tree, advertising_router)
        router_cost = tree.costs[advertising_router]
        for stub in lsa.stub_networks:
            routes.append(
                OSPFRoute(
                    prefix=stub.prefix,
                    next_hop_router_id=next_hop,
                    total_cost=router_cost + stub.metric,
                    area_id=lsa.area_id,
                    route_type="intra_area",
                )
            )

    return tuple(
        sorted(
            routes,
            key=lambda route: (route.prefix, route.total_cost, route.next_hop_router_id, route.area_id),
        )
    )
