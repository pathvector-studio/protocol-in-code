from __future__ import annotations

import heapq
from dataclasses import dataclass

from .lsa import RouterLSA


@dataclass(frozen=True)
class SPFTree:
    root_router_id: str
    costs: dict[str, int]
    parents: dict[str, str | None]
    order: tuple[str, ...]


def build_graph(lsas: tuple[RouterLSA, ...]) -> dict[str, dict[str, int]]:
    graph: dict[str, dict[str, int]] = {}
    for lsa in lsas:
        router_id = lsa.header.advertising_router
        graph.setdefault(router_id, {})
        for link in lsa.links:
            current = graph[router_id].get(link.neighbor_router_id)
            if current is None or link.metric < current:
                graph[router_id][link.neighbor_router_id] = link.metric
    return graph


def shortest_path_tree(lsas: tuple[RouterLSA, ...], root_router_id: str) -> SPFTree:
    graph = build_graph(lsas)
    graph.setdefault(root_router_id, {})

    costs: dict[str, int] = {root_router_id: 0}
    parents: dict[str, str | None] = {root_router_id: None}
    order: list[str] = []
    queue: list[tuple[int, str]] = [(0, root_router_id)]

    while queue:
        current_cost, router_id = heapq.heappop(queue)
        if current_cost != costs.get(router_id):
            continue
        order.append(router_id)

        for neighbor_router_id, edge_cost in graph.get(router_id, {}).items():
            candidate_cost = current_cost + edge_cost
            if candidate_cost < costs.get(neighbor_router_id, 10**9):
                costs[neighbor_router_id] = candidate_cost
                parents[neighbor_router_id] = router_id
                heapq.heappush(queue, (candidate_cost, neighbor_router_id))

    return SPFTree(
        root_router_id=root_router_id,
        costs=costs,
        parents=parents,
        order=tuple(order),
    )

