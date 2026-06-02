from __future__ import annotations

from .best_path import PathCandidate, select_best_path
from .ribs import (
    AdjRIBIn,
    LocRIB,
    build_candidates,
    install_best_path,
    remove_best_path,
)


def recompute_best_path_for_prefix(
    adj_rib_in: AdjRIBIn,
    loc_rib: LocRIB,
    prefix: str,
) -> PathCandidate | None:
    candidates = build_candidates(adj_rib_in, prefix)
    if not candidates:
        remove_best_path(loc_rib, prefix)
        return None

    best = select_best_path(candidates)
    install_best_path(loc_rib, best)
    return best


def handle_peer_loss(
    adj_rib_in: AdjRIBIn,
    loc_rib: LocRIB,
    peer_id: str,
) -> dict[str, PathCandidate | None]:
    lost_prefixes = tuple(adj_rib_in.paths_by_peer.get(peer_id, {}).keys())
    adj_rib_in.paths_by_peer.pop(peer_id, None)

    results: dict[str, PathCandidate | None] = {}
    for prefix in lost_prefixes:
        results[prefix] = recompute_best_path_for_prefix(adj_rib_in, loc_rib, prefix)
    return results
