from __future__ import annotations

from dataclasses import dataclass, field

from .best_path import PathCandidate
from .update import PathAttributes


def origin_to_origin_type(origin: str) -> int:
    order = {
        "igp": 0,
        "egp": 1,
        "incomplete": 2,
    }
    return order.get(origin.lower(), 2)


@dataclass
class AdjRIBIn:
    paths_by_peer: dict[str, dict[str, PathAttributes]] = field(default_factory=dict)


@dataclass
class LocRIB:
    best_paths: dict[str, PathCandidate] = field(default_factory=dict)


@dataclass
class AdjRIBOut:
    advertisements_by_peer: dict[str, dict[str, PathCandidate]] = field(default_factory=dict)


def store_received_path(
    adj_rib_in: AdjRIBIn,
    peer_id: str,
    prefix: str,
    attributes: PathAttributes,
) -> None:
    adj_rib_in.paths_by_peer.setdefault(peer_id, {})[prefix] = attributes


def received_attributes_for_prefix(
    adj_rib_in: AdjRIBIn,
    prefix: str,
) -> list[tuple[str, PathAttributes]]:
    received: list[tuple[str, PathAttributes]] = []
    for peer_id, attributes_by_prefix in adj_rib_in.paths_by_peer.items():
        attributes = attributes_by_prefix.get(prefix)
        if attributes is None:
            continue
        received.append((peer_id, attributes))
    return received


def withdraw_received_path(adj_rib_in: AdjRIBIn, peer_id: str, prefix: str) -> None:
    peer_table = adj_rib_in.paths_by_peer.get(peer_id)
    if peer_table is None:
        return

    peer_table.pop(prefix, None)
    if not peer_table:
        adj_rib_in.paths_by_peer.pop(peer_id, None)


def build_candidates(adj_rib_in: AdjRIBIn, prefix: str) -> list[PathCandidate]:
    candidates: list[PathCandidate] = []
    for _, attributes in received_attributes_for_prefix(adj_rib_in, prefix):
        candidates.append(candidate_from_attributes(prefix, attributes))
    return candidates


def candidate_from_attributes(prefix: str, attributes: PathAttributes) -> PathCandidate:
    return PathCandidate(
        prefix=prefix,
        next_hop=attributes.next_hop,
        local_pref=attributes.local_pref,
        as_path=attributes.as_path,
        origin_type=origin_to_origin_type(attributes.origin),
    )


def install_best_path(loc_rib: LocRIB, best_path: PathCandidate) -> None:
    loc_rib.best_paths[best_path.prefix] = best_path


def remove_best_path(loc_rib: LocRIB, prefix: str) -> None:
    loc_rib.best_paths.pop(prefix, None)


def stage_advertisement(
    adj_rib_out: AdjRIBOut,
    peer_id: str,
    path: PathCandidate,
) -> None:
    adj_rib_out.advertisements_by_peer.setdefault(peer_id, {})[path.prefix] = path


def withdraw_staged_advertisement(
    adj_rib_out: AdjRIBOut,
    peer_id: str,
    prefix: str,
) -> None:
    peer_table = adj_rib_out.advertisements_by_peer.get(peer_id)
    if peer_table is None:
        return

    peer_table.pop(prefix, None)
    if not peer_table:
        adj_rib_out.advertisements_by_peer.pop(peer_id, None)
