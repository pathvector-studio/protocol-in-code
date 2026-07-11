"""Ports have roles.

Once a bridge knows the root (root_election.py) and can compare paths and
BPDUs (path_cost.py, blocking.py), it assigns every port exactly one role.
The root bridge is easy - every one of its ports is DESIGNATED, because
nothing can offer a better path to root than being the root. Every other
bridge needs exactly one ROOT_PORT (the port facing its own best path to
root) and, on every other port, either DESIGNATED (we are the best speaker
for that segment) or BLOCKED (someone else already is).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .blocking import Bpdu, should_block


class PortRole(str, Enum):
    ROOT_PORT = "Root Port"
    DESIGNATED = "Designated"
    BLOCKED = "Blocked"


@dataclass(frozen=True)
class PortView:
    port_id: int
    heard: Bpdu | None
    my_offer: Bpdu


def assign_roles(ports: tuple[PortView, ...], i_am_root: bool) -> dict[int, PortRole]:
    """Assign every port in `ports` a role.

    Root bridge: every port is DESIGNATED - there is no better path to
    itself, so it never defers.

    Non-root bridge: the port with the lowest my_offer.root_path_cost is the
    ROOT_PORT (best_path picks it via path_cost.better_path's ordering, here
    reduced to the cost each port's own offer already encodes). Every other
    port is DESIGNATED if our offer beats what we hear there, or BLOCKED if
    the segment already has a better speaker.
    """
    if i_am_root:
        return {port.port_id: PortRole.DESIGNATED for port in ports}

    root_port_id = min(ports, key=lambda port: port.my_offer.root_path_cost).port_id

    roles: dict[int, PortRole] = {}
    for port in ports:
        if port.port_id == root_port_id:
            roles[port.port_id] = PortRole.ROOT_PORT
        elif port.heard is not None and should_block(port.heard, port.my_offer):
            roles[port.port_id] = PortRole.BLOCKED
        else:
            roles[port.port_id] = PortRole.DESIGNATED

    root_ports = [port_id for port_id, role in roles.items() if role is PortRole.ROOT_PORT]
    assert len(root_ports) == 1, "a non-root bridge must have exactly one root port"

    return roles
