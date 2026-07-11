"""Election is a comparison function, five times.

BGP's best-path selection, OSPF's DR election, RIP's route preference,
VRRP's master election, and STP's root election all reduce to the same
move: build a comparison key per candidate and take an extreme. Four of
the five take the max (highest key wins); STP alone takes the min (lowest
key wins) - the deliberate inversion this file's second function names.
Every election below calls the package's own real comparison function,
not a re-implementation of it.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..bgp.best_path import PathCandidate, select_best_path
from ..ha.vrrp_election import VrrpRouter, elect as vrrp_elect
from ..ospf.dr_election import InterfaceCandidate, elect_dr_bdr
from ..rip.route import RipRoute, better as rip_better
from ..stp.root_election import BridgeId, elect_root


@dataclass(frozen=True)
class ElectionDemo:
    protocol: str
    direction: str
    key_description: str
    winner: str


def demonstrate_all() -> tuple[ElectionDemo, ...]:
    rows: list[ElectionDemo] = []

    # --- BGP: best path among candidates for one prefix, highest attrs win --
    paths = [
        PathCandidate(prefix="10.0.0.0/24", next_hop="192.0.2.1", weight=0, local_pref=100, as_path=(65002, 65003)),
        PathCandidate(prefix="10.0.0.0/24", next_hop="192.0.2.2", weight=0, local_pref=200, as_path=(65004,)),
        PathCandidate(prefix="10.0.0.0/24", next_hop="192.0.2.3", weight=0, local_pref=200, as_path=(65005, 65006)),
    ]
    best = select_best_path(paths)
    rows.append(
        ElectionDemo(
            "bgp",
            "highest wins",
            "(weight, local_pref, -len(as_path), -origin_type, next_hop)",
            best.next_hop,
        )
    )

    # --- OSPF: designated router among interface candidates, highest wins --
    candidates = (
        InterfaceCandidate(router_id="1.1.1.1", priority=1),
        InterfaceCandidate(router_id="2.2.2.2", priority=10),
        InterfaceCandidate(router_id="3.3.3.3", priority=10),
    )
    result = elect_dr_bdr(candidates)
    rows.append(
        ElectionDemo(
            "ospf",
            "highest wins",
            "(priority, router_id)",
            result.designated_router or "",
        )
    )

    # --- RIP: preferred route among two rumors for the same prefix, lowest metric wins
    route_a = RipRoute(prefix="10.0.0.0/24", metric=4, next_hop="10.1.1.1", learned_from="10.1.1.1")
    route_b = RipRoute(prefix="10.0.0.0/24", metric=2, next_hop="10.1.1.2", learned_from="10.1.1.2")
    winner = route_a if rip_better(route_a, route_b) else route_b
    rows.append(
        ElectionDemo(
            "rip",
            "lowest wins",
            "metric",
            winner.next_hop,
        )
    )

    # --- VRRP: master among routers sharing a virtual IP, highest wins ------
    routers = (
        VrrpRouter(name="r1", priority=100, primary_ip="10.0.0.1"),
        VrrpRouter(name="r2", priority=150, primary_ip="10.0.0.2"),
        VrrpRouter(name="r3", priority=150, primary_ip="10.0.0.3"),
    )
    master = vrrp_elect(routers)
    rows.append(
        ElectionDemo(
            "vrrp",
            "highest wins",
            "(priority, primary_ip)",
            master.name,
        )
    )

    # --- STP: root bridge among bridge IDs, lowest wins ----------------------
    bridge_ids = (
        BridgeId(priority=32768, mac="aa:bb:cc:00:00:01"),
        BridgeId(priority=4096, mac="aa:bb:cc:00:00:02"),
        BridgeId(priority=4096, mac="aa:bb:cc:00:00:01"),
    )
    root = elect_root(bridge_ids)
    rows.append(
        ElectionDemo(
            "stp",
            "lowest wins",
            "(priority, mac)",
            root.mac,
        )
    )

    return tuple(rows)


def the_inversion() -> str:
    """OSPF, VRRP, and RIP all take the max of a comparison key; STP alone takes the min.

    Same (priority, id)-shaped tuple, opposite sign - swap max() for min() (or vice
    versa) while porting election logic between these modules and every candidate's
    rank silently flips, the classic off-by-inversion bug this course's STP thesis
    docstring (stp/root_election.py) names outright.
    """
    return (
        "OSPF, RIP, and VRRP elect by taking the max of a comparison key (highest wins); "
        "STP elects by taking the min of the same shape of key (lowest wins) - same shape, "
        "opposite sign, and swapping max() for min() while porting one module's election "
        "logic into another is the classic bug this inversion sets up."
    )
