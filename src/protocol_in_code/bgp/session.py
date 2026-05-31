from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SessionState(str, Enum):
    IDLE = "Idle"
    CONNECT = "Connect"
    ACTIVE = "Active"
    OPEN_SENT = "OpenSent"
    OPEN_CONFIRM = "OpenConfirm"
    ESTABLISHED = "Established"


@dataclass(frozen=True)
class BGPCapability:
    name: str
    enabled: bool = True


@dataclass(frozen=True)
class BGPSessionConfig:
    peer_ip: str
    peer_as: int
    local_as: int
    tcp_reachable: bool
    hold_time: int = 180
    keepalive_time: int = 60
    capabilities: tuple[BGPCapability, ...] = field(default_factory=tuple)
    open_message_ok: bool = True
    keepalive_received: bool = True


def establish_neighbor(config: BGPSessionConfig) -> SessionState:
    """Walk a minimal BGP session state machine."""
    state = SessionState.IDLE

    if not config.peer_ip:
        return state

    state = SessionState.CONNECT
    if not config.tcp_reachable:
        return SessionState.ACTIVE

    state = SessionState.OPEN_SENT
    if config.peer_as <= 0 or config.local_as <= 0:
        return state
    if not config.open_message_ok:
        return state

    state = SessionState.OPEN_CONFIRM
    if not config.keepalive_received:
        return state

    return SessionState.ESTABLISHED
