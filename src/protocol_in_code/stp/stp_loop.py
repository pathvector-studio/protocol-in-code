"""Build the toy spanning tree loop.

A ToyStpBridge owns a bridge_id, a set of ports (each wired to a named
segment shared with other bridges), and the best BPDU it has heard on each
port so far. Each round every bridge works out its own cost to root from
what it heard last round, emits a BPDU stamped with that cost on every port
that isn't BLOCKED (path_cost.py's accumulate() rule - the cost is charged
on the receiving end, so what we emit here is the cost as WE see it, before
our neighbor adds their own hop), and every bridge on the far end of that
segment receives it. converge() round-robins this exchange - elect the root
(root_election.py), keep each port's best-heard BPDU (blocking.py), and
re-derive port roles (port_roles.py) - until nobody's picture of the network
changes.

The payoff is the triangle demo: three bridges wired A-B, B-C, C-A all share
one physical loop, but converge() leaves exactly one port BLOCKED. That
blocked port is not wasted - it is the network's spare tire. fail_root()
proves it: take down the root, force a re-election, and the port that used
to sit idle because a better speaker already covered its segment picks up
the slack the moment the topology actually needs it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .blocking import Bpdu, bpdu_is_superior
from .path_cost import PORT_COST
from .root_election import BridgeId, elect_root

DEFAULT_SPEED_MBPS = 100
"""Every link in the toy triangle runs at this speed, so PORT_COST[100] == 19
is the accumulation charged on every hop."""


@dataclass
class ToyStpBridge:
    bridge_id: BridgeId
    ports: dict[int, str] = field(default_factory=dict)
    best_bpdu_heard: dict[int, Bpdu] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    blocked_ports: set[int] = field(default_factory=set)

    def cost_to_root(self, root: BridgeId) -> int:
        """This bridge's best known root_path_cost, from whatever it has heard so far.
        Zero if this bridge IS the root, or if it has not heard from the root yet."""
        if self.bridge_id == root:
            return 0
        heard_costs = [bpdu.root_path_cost for bpdu in self.best_bpdu_heard.values() if bpdu.root_id == root]
        return min(heard_costs) if heard_costs else 0

    def root_port_id(self, root: BridgeId) -> int | None:
        """The port whose heard BPDU carries the lowest root_path_cost - our best path to root.
        None for the root bridge itself, or if nothing has been heard yet."""
        candidates = {port_id: bpdu.root_path_cost for port_id, bpdu in self.best_bpdu_heard.items() if bpdu.root_id == root}
        if not candidates:
            return None
        return min(candidates, key=lambda port_id: candidates[port_id])

    def emit_bpdus(self, root: BridgeId) -> dict[int, Bpdu]:
        """One outbound BPDU per non-blocked port, stamped with this bridge as sender and
        its own current cost to root - the cost accumulates when the NEXT bridge receives it
        (path_cost.accumulate), not here."""
        cost = self.cost_to_root(root)
        return {
            port_id: Bpdu(root_id=root, root_path_cost=cost, sender_bridge=self.bridge_id, sender_port=port_id)
            for port_id in self.ports
            if port_id not in self.blocked_ports
        }

    def receive(self, port_id: int, bpdu: Bpdu) -> None:
        """Add this port's ingress cost to the BPDU's claim, then keep it only if that's
        better than whatever this port has heard before (blocking.bpdu_is_superior)."""
        arrived = Bpdu(
            root_id=bpdu.root_id,
            root_path_cost=bpdu.root_path_cost + PORT_COST[DEFAULT_SPEED_MBPS],
            sender_bridge=bpdu.sender_bridge,
            sender_port=bpdu.sender_port,
        )
        current = self.best_bpdu_heard.get(port_id)
        if current is None or bpdu_is_superior(arrived, current):
            self.best_bpdu_heard[port_id] = arrived
            self.trace.append(f"{self.bridge_id.mac}: port {port_id} now hears root={arrived.root_id.mac} cost={arrived.root_path_cost}")

    def recompute_blocked(self, root: BridgeId) -> None:
        """Re-derive this bridge's blocked ports: the root blocks nothing, everyone else
        keeps their root port open and blocks any other port where the segment's best
        heard BPDU beats what we would send there ourselves."""
        if self.bridge_id == root:
            self.blocked_ports = set()
            return

        root_port = self.root_port_id(root)
        my_cost = self.cost_to_root(root)
        blocked: set[int] = set()
        for port_id, heard in self.best_bpdu_heard.items():
            if port_id == root_port:
                continue
            my_offer = Bpdu(root_id=root, root_path_cost=my_cost, sender_bridge=self.bridge_id, sender_port=port_id)
            if bpdu_is_superior(heard, my_offer):
                blocked.add(port_id)
        self.blocked_ports = blocked


@dataclass(frozen=True)
class ConvergenceReport:
    root: BridgeId
    blocked_ports: tuple[tuple[str, int], ...]
    rounds_run: int


def _exchange_round(bridges: dict[str, ToyStpBridge], segments: dict[str, list[tuple[str, int]]], root: BridgeId) -> bool:
    """One round: every bridge emits on its open ports, every peer sharing that segment
    receives. Returns True if any bridge's best-heard BPDU changed."""
    outgoing: dict[tuple[str, int], Bpdu] = {}
    for name, bridge in bridges.items():
        for port_id, bpdu in bridge.emit_bpdus(root).items():
            outgoing[(name, port_id)] = bpdu

    changed = False
    for members in segments.values():
        for name, port_id in members:
            bridge = bridges[name]
            for sender_name, sender_port in members:
                if sender_name == name and sender_port == port_id:
                    continue
                bpdu = outgoing.get((sender_name, sender_port))
                if bpdu is None:
                    continue
                before = bridge.best_bpdu_heard.get(port_id)
                bridge.receive(port_id, bpdu)
                if bridge.best_bpdu_heard.get(port_id) != before:
                    changed = True

    for bridge in bridges.values():
        bridge.recompute_blocked(root)

    return changed


def converge(bridges: dict[str, ToyStpBridge], segments: dict[str, list[tuple[str, int]]], rounds: int) -> ConvergenceReport:
    """Elect the root, then exchange BPDUs round by round until nobody's picture changes."""
    root = elect_root(tuple(bridge.bridge_id for bridge in bridges.values()))

    for round_no in range(1, rounds + 1):
        changed = _exchange_round(bridges, segments, root)
        if not changed:
            return ConvergenceReport(root=root, blocked_ports=_blocked_snapshot(bridges), rounds_run=round_no)

    return ConvergenceReport(root=root, blocked_ports=_blocked_snapshot(bridges), rounds_run=rounds)


def _blocked_snapshot(bridges: dict[str, ToyStpBridge]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted((name, port_id) for name, bridge in bridges.items() for port_id in bridge.blocked_ports))


def triangle() -> tuple[dict[str, ToyStpBridge], dict[str, list[tuple[str, int]]]]:
    """Three bridges, three segments, one loop: A-B, B-C, C-A.

    A is lowest priority (root by design, not by MAC accident). Each bridge
    has two ports, one per segment it touches.
    """
    bridge_a = ToyStpBridge(bridge_id=BridgeId(priority=4096, mac="00:00:00:00:00:0a"), ports={1: "seg-ab", 2: "seg-ca"})
    bridge_b = ToyStpBridge(bridge_id=BridgeId(priority=32768, mac="00:00:00:00:00:0b"), ports={1: "seg-ab", 2: "seg-bc"})
    bridge_c = ToyStpBridge(bridge_id=BridgeId(priority=32768, mac="00:00:00:00:00:0c"), ports={1: "seg-bc", 2: "seg-ca"})

    bridges = {"A": bridge_a, "B": bridge_b, "C": bridge_c}
    segments = {
        "seg-ab": [("A", 1), ("B", 1)],
        "seg-bc": [("B", 2), ("C", 1)],
        "seg-ca": [("C", 2), ("A", 2)],
    }
    return bridges, segments


def fail_root(bridges: dict[str, ToyStpBridge], segments: dict[str, list[tuple[str, int]]], failed_name: str, rounds: int) -> ConvergenceReport:
    """Remove `failed_name` from the topology and re-converge: a new root is elected, and
    the port that used to be BLOCKED because the old root's traffic already covered its
    segment is free to pick up the work - the spare tire gets used."""
    surviving_bridges = {name: bridge for name, bridge in bridges.items() if name != failed_name}
    for bridge in surviving_bridges.values():
        bridge.best_bpdu_heard = {}
        bridge.blocked_ports = set()

    surviving_segments = {
        segment_name: [(name, port_id) for name, port_id in members if name != failed_name]
        for segment_name, members in segments.items()
    }
    surviving_segments = {name: members for name, members in surviving_segments.items() if len(members) >= 2}

    return converge(surviving_bridges, surviving_segments, rounds)
