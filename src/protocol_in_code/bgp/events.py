from __future__ import annotations

from dataclasses import dataclass

from .best_path import PathCandidate
from .decision_process import select_best_installable_for_prefix
from .export_refresh import ExportChange, ExportTarget, refresh_exports_for_prefix
from .peer_state import PeerSession, receive_update_if_established
from .pipeline import PipelinePolicies
from .ribs import AdjRIBIn, AdjRIBOut, LocRIB, install_best_path, remove_best_path, withdraw_received_path
from .session import SessionState
from .update import PathAttributes
from .validation import VRP


@dataclass(frozen=True)
class AnnounceEvent:
    peer_id: str
    prefix: str
    attributes: PathAttributes


@dataclass(frozen=True)
class WithdrawEvent:
    peer_id: str
    prefix: str


@dataclass(frozen=True)
class PeerDownEvent:
    peer_id: str


@dataclass(frozen=True)
class EventResult:
    accepted: bool
    touched_prefixes: tuple[str, ...]
    best_paths: dict[str, PathCandidate | None]
    export_changes: tuple[ExportChange, ...]


def _recompute_prefix(
    adj_rib_in: AdjRIBIn,
    loc_rib: LocRIB,
    prefix: str,
    vrps: list[VRP],
    policies: PipelinePolicies,
) -> PathCandidate | None:
    best = select_best_installable_for_prefix(adj_rib_in, prefix, vrps, policies)
    if best is None:
        remove_best_path(loc_rib, prefix)
        return None

    install_best_path(loc_rib, best)
    return best


def process_announce_event(
    event: AnnounceEvent,
    peers: dict[str, PeerSession],
    adj_rib_in: AdjRIBIn,
    loc_rib: LocRIB,
    adj_rib_out: AdjRIBOut,
    export_targets: tuple[ExportTarget, ...],
    vrps: list[VRP],
    policies: PipelinePolicies,
) -> EventResult:
    peer = peers[event.peer_id]
    accepted = receive_update_if_established(adj_rib_in, peer, event.prefix, event.attributes)
    if not accepted:
        return EventResult(
            accepted=False,
            touched_prefixes=(event.prefix,),
            best_paths={event.prefix: loc_rib.best_paths.get(event.prefix)},
            export_changes=(),
        )

    best = _recompute_prefix(adj_rib_in, loc_rib, event.prefix, vrps, policies)
    changes = refresh_exports_for_prefix(event.prefix, loc_rib, adj_rib_out, export_targets)
    return EventResult(
        accepted=True,
        touched_prefixes=(event.prefix,),
        best_paths={event.prefix: best},
        export_changes=tuple(changes),
    )


def process_withdraw_event(
    event: WithdrawEvent,
    adj_rib_in: AdjRIBIn,
    loc_rib: LocRIB,
    adj_rib_out: AdjRIBOut,
    export_targets: tuple[ExportTarget, ...],
    vrps: list[VRP],
    policies: PipelinePolicies,
) -> EventResult:
    withdraw_received_path(adj_rib_in, event.peer_id, event.prefix)
    best = _recompute_prefix(adj_rib_in, loc_rib, event.prefix, vrps, policies)
    changes = refresh_exports_for_prefix(event.prefix, loc_rib, adj_rib_out, export_targets)
    return EventResult(
        accepted=True,
        touched_prefixes=(event.prefix,),
        best_paths={event.prefix: best},
        export_changes=tuple(changes),
    )


def process_peer_down_event(
    event: PeerDownEvent,
    peers: dict[str, PeerSession],
    adj_rib_in: AdjRIBIn,
    loc_rib: LocRIB,
    adj_rib_out: AdjRIBOut,
    export_targets: tuple[ExportTarget, ...],
    vrps: list[VRP],
    policies: PipelinePolicies,
) -> EventResult:
    lost_prefixes = tuple(adj_rib_in.paths_by_peer.get(event.peer_id, {}).keys())
    adj_rib_in.paths_by_peer.pop(event.peer_id, None)
    peer = peers.get(event.peer_id)
    if peer is not None:
        peers[event.peer_id] = PeerSession(peer_id=peer.peer_id, config=peer.config, state=SessionState.ACTIVE)

    lost: dict[str, PathCandidate | None] = {}
    changes: list[ExportChange] = []
    for prefix in lost_prefixes:
        lost[prefix] = _recompute_prefix(adj_rib_in, loc_rib, prefix, vrps, policies)
        changes.extend(refresh_exports_for_prefix(prefix, loc_rib, adj_rib_out, export_targets))

    return EventResult(
        accepted=True,
        touched_prefixes=tuple(lost.keys()),
        best_paths=lost,
        export_changes=tuple(changes),
    )
