from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .lsa import RouterLSA, is_newer_lsa


class InterfaceState(str, Enum):
    DOWN = "Down"
    WAITING = "Waiting"
    DROTHER = "DROther"
    EXCHANGE = "Exchange"
    FULL = "Full"


@dataclass(frozen=True)
class FloodInterface:
    name: str
    state: InterfaceState
    neighbor_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class FloodDecision:
    newer: bool
    acknowledge_to_sender: bool
    outgoing_interfaces: tuple[str, ...]


def flood_lsa(
    incoming_interface: str,
    interfaces: tuple[FloodInterface, ...],
    received_lsa: RouterLSA,
    current_lsa: RouterLSA | None = None,
) -> FloodDecision:
    newer = current_lsa is None or is_newer_lsa(received_lsa, current_lsa)
    if not newer:
        return FloodDecision(newer=False, acknowledge_to_sender=True, outgoing_interfaces=())

    floodable_states = {InterfaceState.EXCHANGE, InterfaceState.FULL}
    outgoing = tuple(
        interface.name
        for interface in interfaces
        if interface.name != incoming_interface and interface.state in floodable_states
    )
    return FloodDecision(newer=True, acknowledge_to_sender=True, outgoing_interfaces=outgoing)

