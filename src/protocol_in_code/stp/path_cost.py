"""Cost decides the path to root.

Once every bridge agrees who the root is (root_election.py), each bridge
still has to pick which of its own ports leads there by the cheapest route.
802.1D scores link speed as an inverse cost - faster links cost less - so
that a spanning tree naturally prefers high-bandwidth paths over slow ones.
"""

from __future__ import annotations

from dataclasses import dataclass

from .root_election import BridgeId, bridge_id_lt

PORT_COST = {
    10: 100,
    100: 19,
    1000: 4,
    10000: 2,
}
"""The classic 802.1D port cost table, keyed by link speed in Mbps. Cost falls
as speed rises: a 10 Mbps hop costs 100, a 10 Gbps hop costs 2. Unlisted
speeds have no defined cost here - a real implementation interpolates or
falls back to 802.1D-2004's revised (higher-precision) table."""


@dataclass(frozen=True)
class PathToRoot:
    root_path_cost: int
    neighbor_bridge: BridgeId
    neighbor_port_id: int


def accumulate(path: PathToRoot, ingress_speed_mbps: int) -> int:
    """Add the cost of the port a BPDU just arrived on to the cost it already carried.

    Cost accumulates on the RECEIVING side, not the sending side: a BPDU
    advertises the cost of the path from the root down to its sender, and the
    bridge that hears it adds the cost of the link it just came IN on before
    advertising that total onward. This is a common point of confusion -
    it's tempting to charge the cost to the port that transmits, but 802.1D
    charges the port that receives.
    """
    return path.root_path_cost + PORT_COST[ingress_speed_mbps]


def better_path(a: PathToRoot, b: PathToRoot) -> bool:
    """Is `a` the preferred path to root over `b`?

    An ordered tiebreak chain, each stage a separate branch so the priority
    order is visible rather than folded into one tuple comparison:

    1. Lower root_path_cost wins outright.
    2. Cost tied: the path heard from the lower neighbor bridge ID wins.
    3. Neighbor bridge also tied (two parallel links to the same neighbor):
       the lower neighbor_port_id wins.
    """
    if a.root_path_cost != b.root_path_cost:
        return a.root_path_cost < b.root_path_cost

    if a.neighbor_bridge != b.neighbor_bridge:
        return bridge_id_lt(a.neighbor_bridge, b.neighbor_bridge)

    return a.neighbor_port_id < b.neighbor_port_id
