from __future__ import annotations

from dataclasses import dataclass

from .cost import select_best_routes
from .lsa import RouterLSA
from .lsdb import LinkStateDatabase
from .routing import OSPFRoute, routes_from_tree
from .spf import shortest_path_tree


@dataclass(frozen=True)
class RecomputeResult:
    installed: bool
    routes_before: tuple[OSPFRoute, ...]
    routes_after: tuple[OSPFRoute, ...]
    changed_prefixes: tuple[str, ...]


def recompute_area_routes(
    lsdb: LinkStateDatabase,
    root_router_id: str,
    area_id: str,
) -> tuple[OSPFRoute, ...]:
    lsas = lsdb.router_lsas(area_id)
    tree = shortest_path_tree(lsas, root_router_id)
    candidate_routes = routes_from_tree(root_router_id, tree, lsas)
    return select_best_routes(candidate_routes)


def _route_index(routes: tuple[OSPFRoute, ...]) -> dict[str, OSPFRoute]:
    return {route.prefix: route for route in routes}


def apply_router_lsa(
    lsdb: LinkStateDatabase,
    root_router_id: str,
    lsa: RouterLSA,
) -> RecomputeResult:
    before = recompute_area_routes(lsdb, root_router_id, lsa.area_id)
    installed = lsdb.install_router_lsa(lsa)
    after = recompute_area_routes(lsdb, root_router_id, lsa.area_id)

    before_index = _route_index(before)
    after_index = _route_index(after)
    changed = sorted(
        prefix
        for prefix in set(before_index) | set(after_index)
        if before_index.get(prefix) != after_index.get(prefix)
    )

    return RecomputeResult(
        installed=installed,
        routes_before=before,
        routes_after=after,
        changed_prefixes=tuple(changed),
    )

