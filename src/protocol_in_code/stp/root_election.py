"""The root is the lowest ID.

STP (802.1D) elects a root bridge the same way OSPF elects a designated
router (see ospf/dr_election.py) and VRRP elects a master (see
ha/vrrp_election.py): rank every candidate by a comparison key and take the
extreme. Same election-by-comparison shape, but the direction is inverted -
OSPF and VRRP take the max() of (priority, id), STP takes the min(). Elsewhere
"more preferred" means "numerically bigger"; in spanning tree it means
"numerically smaller." There is no protocol reason for the flip, it is just
what the standard picked, and it is a classic source of off-by-inversion bugs
when porting election logic between these three modules.

The operational consequence is worth stating plainly: if every bridge keeps
the default priority (32768), the tiebreak falls entirely to the MAC address,
and MAC addresses sort low-to-high in manufacture order for a given vendor
block. The bridge that has been running longest - usually the oldest switch
on the network - tends to have the lowest MAC and becomes root by accident.
Explicit priority configuration exists so a human can override that accident
and put a deliberately chosen, well-connected switch at the center of the
tree instead of whichever box happens to be the oldest.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_PRIORITY = 32768
"""802.1D's factory-default bridge priority. Every bridge shipping with this
same value is exactly how the "oldest MAC becomes root by accident" scenario
happens - with priority tied, mac is the only thing left to compare."""


def _mac_key(mac: str) -> tuple[int, ...]:
    return tuple(int(octet, 16) for octet in mac.split(":"))


@dataclass(frozen=True)
class BridgeId:
    priority: int
    mac: str


def bridge_id_lt(a: BridgeId, b: BridgeId) -> bool:
    """Total order over bridge IDs: (priority, mac) compared as a tuple, lowest wins.

    This is the inversion point against ospf/dr_election.py and
    ha/vrrp_election.py: those modules build the same (priority, id) tuple and
    call max(); STP builds it and effectively wants min(). `a < b` here means
    "a is MORE preferred," which reads backwards next to the other two
    modules on purpose - it is the whole thesis of this file.
    """
    return (a.priority, _mac_key(a.mac)) < (b.priority, _mac_key(b.mac))


def elect_root(bridge_ids: tuple[BridgeId, ...]) -> BridgeId:
    """The root bridge is whichever BridgeId is lowest - by priority first, then by MAC.

    Ties on priority fall to the MAC address, which is why an unconfigured
    network (every bridge at DEFAULT_PRIORITY) elects its oldest switch: low
    MACs cluster in early manufacturing runs. A network operator who wants a
    specific bridge at the root sets that bridge's priority below
    DEFAULT_PRIORITY, which wins the comparison before mac is ever consulted.
    """
    return min(bridge_ids, key=lambda bridge_id: (bridge_id.priority, _mac_key(bridge_id.mac)))
