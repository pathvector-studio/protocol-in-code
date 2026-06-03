from __future__ import annotations

from dataclasses import dataclass, field

from .best_path import PathCandidate
from .events import (
    AnnounceEvent,
    EventResult,
    PeerDownEvent,
    WithdrawEvent,
    process_announce_event,
    process_peer_down_event,
    process_withdraw_event,
)
from .export_refresh import ExportChange, ExportTarget
from .peer_state import PeerSession, open_peer_session
from .pipeline import PipelinePolicies
from .ribs import AdjRIBIn, AdjRIBOut, LocRIB
from .session import BGPSessionConfig
from .update import PathAttributes
from .validation import VRP


@dataclass(frozen=True)
class SpeakerStep:
    event: str
    accepted: bool
    prefixes: tuple[str, ...]
    installed_paths: dict[str, PathCandidate | None]
    export_changes: tuple[ExportChange, ...]


@dataclass
class ToyBGPSpeaker:
    vrps: list[VRP]
    policies: PipelinePolicies
    adj_rib_in: AdjRIBIn = field(default_factory=AdjRIBIn)
    loc_rib: LocRIB = field(default_factory=LocRIB)
    adj_rib_out: AdjRIBOut = field(default_factory=AdjRIBOut)
    peers: dict[str, PeerSession] = field(default_factory=dict)
    export_targets: dict[str, ExportTarget] = field(default_factory=dict)

    def add_neighbor(self, peer_id: str, config: BGPSessionConfig) -> None:
        self.peers[peer_id] = open_peer_session(peer_id, config)

    def add_export_target(self, target: ExportTarget) -> None:
        self.export_targets[target.peer_id] = target

    def _all_export_targets(self) -> tuple[ExportTarget, ...]:
        return tuple(self.export_targets.values())

    def _step_from_event(self, event: str, result: EventResult) -> SpeakerStep:
        return SpeakerStep(
            event=event,
            accepted=result.accepted,
            prefixes=result.touched_prefixes,
            installed_paths=result.best_paths,
            export_changes=result.export_changes,
        )

    def receive_announce(
        self,
        peer_id: str,
        prefix: str,
        attributes: PathAttributes,
    ) -> SpeakerStep:
        result = process_announce_event(
            AnnounceEvent(peer_id=peer_id, prefix=prefix, attributes=attributes),
            self.peers,
            self.adj_rib_in,
            self.loc_rib,
            self.adj_rib_out,
            self._all_export_targets(),
            self.vrps,
            self.policies,
        )
        return self._step_from_event("announce", result)

    def receive_withdraw(self, peer_id: str, prefix: str) -> SpeakerStep:
        result = process_withdraw_event(
            WithdrawEvent(peer_id=peer_id, prefix=prefix),
            self.adj_rib_in,
            self.loc_rib,
            self.adj_rib_out,
            self._all_export_targets(),
            self.vrps,
            self.policies,
        )
        return self._step_from_event("withdraw", result)

    def peer_down(self, peer_id: str) -> SpeakerStep:
        result = process_peer_down_event(
            PeerDownEvent(peer_id=peer_id),
            self.peers,
            self.adj_rib_in,
            self.loc_rib,
            self.adj_rib_out,
            self._all_export_targets(),
            self.vrps,
            self.policies,
        )
        return self._step_from_event("peer_down", result)
