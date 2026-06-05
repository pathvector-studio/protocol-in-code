from __future__ import annotations

from dataclasses import dataclass, field

from .cost import select_best_routes
from .dr_election import ElectionResult, InterfaceCandidate, elect_dr_bdr
from .flooding import FloodInterface, FloodDecision, InterfaceState, flood_lsa
from .areas import SummaryLSA, import_summary_lsas, summarize_area_routes
from .hello import InterfaceHelloConfig, OSPFHelloPacket, evaluate_hello
from .lsa import RouterLSA
from .lsdb import LinkStateDatabase
from .neighbor import AdjacencyInputs, NeighborState, advance_neighbor_state, advance_on_hello
from .recompute import apply_router_lsa
from .routing import OSPFRoute


@dataclass(frozen=True)
class SpeakerInterface:
    name: str
    area_id: str
    hello_config: InterfaceHelloConfig
    flood_state: InterfaceState = InterfaceState.FULL


@dataclass(frozen=True)
class SpeakerStep:
    event: str
    accepted: bool
    neighbor_states: dict[str, NeighborState]
    routes: tuple[OSPFRoute, ...]
    area_routes_by_area: dict[str, tuple[OSPFRoute, ...]]
    summaries: tuple[SummaryLSA, ...]
    changed_prefixes: tuple[str, ...] = ()
    flooded_interfaces: tuple[str, ...] = ()
    election: ElectionResult | None = None


@dataclass
class ToyOSPFSpeaker:
    router_id: str
    lsdb: LinkStateDatabase = field(default_factory=LinkStateDatabase)
    interfaces: dict[str, SpeakerInterface] = field(default_factory=dict)
    neighbor_states: dict[str, NeighborState] = field(default_factory=dict)
    area_routes: dict[str, tuple[OSPFRoute, ...]] = field(default_factory=dict)
    summary_lsas: tuple[SummaryLSA, ...] = ()
    dr_elections: dict[str, ElectionResult] = field(default_factory=dict)
    abr_costs: dict[str, dict[str, int]] = field(default_factory=dict)

    def add_interface(self, interface: SpeakerInterface) -> None:
        self.interfaces[interface.name] = interface

    def _all_routes(self) -> tuple[OSPFRoute, ...]:
        routes: list[OSPFRoute] = []
        for area_id in sorted(self.area_routes):
            routes.extend(self.area_routes[area_id])
        return select_best_routes(tuple(routes))

    def _step(
        self,
        event: str,
        accepted: bool,
        changed_prefixes: tuple[str, ...] = (),
        flooded_interfaces: tuple[str, ...] = (),
        election: ElectionResult | None = None,
    ) -> SpeakerStep:
        return SpeakerStep(
            event=event,
            accepted=accepted,
            neighbor_states=dict(sorted(self.neighbor_states.items())),
            routes=self._all_routes(),
            area_routes_by_area={area_id: routes for area_id, routes in sorted(self.area_routes.items())},
            summaries=self.summary_lsas,
            changed_prefixes=changed_prefixes,
            flooded_interfaces=flooded_interfaces,
            election=election,
        )

    def register_abr_cost(self, area_id: str, abr_router_id: str, cost: int) -> None:
        self.abr_costs.setdefault(area_id, {})[abr_router_id] = cost

    def _should_form_full_adjacency(
        self,
        interface_name: str,
        peer_router_id: str,
        explicit: bool | None,
    ) -> bool:
        if explicit is not None:
            return explicit

        election = self.dr_elections.get(interface_name)
        if election is None:
            return True

        if self.router_id in {election.designated_router, election.backup_designated_router}:
            return True
        return peer_router_id in {election.designated_router, election.backup_designated_router}

    def run_dr_election(
        self,
        interface_name: str,
        candidates: tuple[InterfaceCandidate, ...],
    ) -> SpeakerStep:
        election = elect_dr_bdr(candidates)
        self.dr_elections[interface_name] = election
        return self._step(event="dr_election", accepted=True, election=election)

    def receive_hello(
        self,
        interface_name: str,
        packet: OSPFHelloPacket,
        should_form_full_adjacency: bool | None = None,
    ) -> SpeakerStep:
        interface = self.interfaces[interface_name]
        check = evaluate_hello(interface.hello_config, packet)
        key = f"{interface_name}:{packet.source_router_id}"
        current = self.neighbor_states.get(key, NeighborState.DOWN)
        should_adjacency = self._should_form_full_adjacency(
            interface_name,
            packet.source_router_id,
            should_form_full_adjacency,
        )
        self.neighbor_states[key] = advance_on_hello(
            current,
            hello_accepted=check.accepted,
            saw_self=check.saw_self,
            should_form_full_adjacency=should_adjacency,
        )
        return self._step(event="hello", accepted=check.accepted)

    def complete_database_exchange(
        self,
        interface_name: str,
        peer_router_id: str,
        *,
        should_form_full_adjacency: bool | None = None,
        database_description_ok: bool = True,
        request_list_empty: bool = True,
        retransmissions_cleared: bool = True,
    ) -> SpeakerStep:
        key = f"{interface_name}:{peer_router_id}"
        current = self.neighbor_states.get(key, NeighborState.DOWN)
        should_adjacency = self._should_form_full_adjacency(
            interface_name,
            peer_router_id,
            should_form_full_adjacency,
        )
        self.neighbor_states[key] = advance_neighbor_state(
            current,
            AdjacencyInputs(
                hello_accepted=current != NeighborState.DOWN,
                saw_self=current != NeighborState.INIT,
                should_form_full_adjacency=should_adjacency,
                database_description_ok=database_description_ok,
                request_list_empty=request_list_empty,
                retransmissions_cleared=retransmissions_cleared,
            ),
        )
        return self._step(event="database_exchange", accepted=self.neighbor_states[key] == NeighborState.FULL)

    def receive_router_lsa(
        self,
        interface_name: str,
        peer_router_id: str,
        lsa: RouterLSA,
    ) -> SpeakerStep:
        key = f"{interface_name}:{peer_router_id}"
        if self.neighbor_states.get(key) != NeighborState.FULL:
            return self._step(event="router_lsa", accepted=False)

        interfaces = tuple(
            FloodInterface(name=name, state=interface.flood_state)
            for name, interface in self.interfaces.items()
            if interface.area_id == lsa.area_id
        )
        flood = flood_lsa(interface_name, interfaces, lsa)
        result = apply_router_lsa(self.lsdb, self.router_id, lsa)
        self.area_routes[lsa.area_id] = result.routes_after
        return self._step(
            event="router_lsa",
            accepted=result.installed,
            changed_prefixes=result.changed_prefixes,
            flooded_interfaces=flood.outgoing_interfaces,
        )

    def originate_router_lsa(self, interface_name: str, lsa: RouterLSA) -> SpeakerStep:
        interfaces = tuple(
            FloodInterface(name=name, state=interface.flood_state)
            for name, interface in self.interfaces.items()
            if interface.area_id == lsa.area_id
        )
        flood = flood_lsa(interface_name, interfaces, lsa)
        result = apply_router_lsa(self.lsdb, self.router_id, lsa)
        self.area_routes[lsa.area_id] = result.routes_after
        return self._step(
            event="originate_router_lsa",
            accepted=result.installed,
            changed_prefixes=result.changed_prefixes,
            flooded_interfaces=flood.outgoing_interfaces,
        )

    def summarize_to_area(self, source_area: str, target_area: str) -> SpeakerStep:
        self.summary_lsas = summarize_area_routes(
            self.area_routes.get(source_area, ()),
            source_area=source_area,
            target_area=target_area,
            abr_router_id=self.router_id,
        )
        return self._step(event="summary_lsa", accepted=True)

    def import_summaries(self, area_id: str, summaries: tuple[SummaryLSA, ...]) -> SpeakerStep:
        existing = self.area_routes.get(area_id, ())
        imported = import_summary_lsas(area_id, summaries, self.abr_costs.get(area_id, {}))
        self.area_routes[area_id] = select_best_routes(existing + imported)
        changed_prefixes = tuple(route.prefix for route in imported)
        return self._step(event="summary_import", accepted=True, changed_prefixes=changed_prefixes)
