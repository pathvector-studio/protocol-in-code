from __future__ import annotations

from dataclasses import dataclass

from .ribs import AdjRIBIn, store_received_path
from .session import BGPSessionConfig, SessionState, establish_neighbor
from .update import PathAttributes


@dataclass(frozen=True)
class PeerSession:
    peer_id: str
    config: BGPSessionConfig
    state: SessionState


def open_peer_session(peer_id: str, config: BGPSessionConfig) -> PeerSession:
    return PeerSession(peer_id=peer_id, config=config, state=establish_neighbor(config))


def session_accepts_updates(peer: PeerSession) -> bool:
    return peer.state is SessionState.ESTABLISHED


def receive_update_if_established(
    adj_rib_in: AdjRIBIn,
    peer: PeerSession,
    prefix: str,
    attributes: PathAttributes,
) -> bool:
    if not session_accepts_updates(peer):
        return False

    store_received_path(adj_rib_in, peer.peer_id, prefix, attributes)
    return True
