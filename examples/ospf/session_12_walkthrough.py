from protocol_in_code.ospf.hello import InterfaceHelloConfig, OSPFHelloPacket
from protocol_in_code.ospf.flooding import InterfaceState
from protocol_in_code.ospf.lsa import LSAHeader, LinkDescription, RouterLSA, StubNetwork
from protocol_in_code.ospf.dr_election import InterfaceCandidate
from protocol_in_code.ospf.speaker import SpeakerInterface, ToyOSPFSpeaker


def main() -> None:
    speaker = ToyOSPFSpeaker(router_id="1.1.1.1")
    speaker.add_interface(
        SpeakerInterface(
            name="eth0",
            area_id="0.0.0.0",
            hello_config=InterfaceHelloConfig(
                local_router_id="1.1.1.1",
                area_id="0.0.0.0",
                netmask="255.255.255.0",
                hello_interval=10,
                dead_interval=40,
            ),
            flood_state=InterfaceState.FULL,
        )
    )
    speaker.add_interface(
        SpeakerInterface(
            name="eth1",
            area_id="0.0.0.0",
            hello_config=InterfaceHelloConfig(
                local_router_id="1.1.1.1",
                area_id="0.0.0.0",
                netmask="255.255.255.0",
                hello_interval=10,
                dead_interval=40,
            ),
            flood_state=InterfaceState.FULL,
        )
    )
    election_step = speaker.run_dr_election(
        "eth0",
        (
            InterfaceCandidate(router_id="1.1.1.1", priority=1),
            InterfaceCandidate(router_id="2.2.2.2", priority=100, declared_dr=True),
            InterfaceCandidate(router_id="3.3.3.3", priority=50, declared_bdr=True),
        ),
    )

    hello_step = speaker.receive_hello(
        "eth0",
        OSPFHelloPacket(
            source_router_id="2.2.2.2",
            area_id="0.0.0.0",
            netmask="255.255.255.0",
            hello_interval=10,
            dead_interval=40,
            priority=1,
            designated_router=None,
            backup_designated_router=None,
            neighbors=("1.1.1.1",),
        ),
    )
    exchange_step = speaker.complete_database_exchange(
        "eth0",
        "2.2.2.2",
        database_description_ok=True,
        request_list_empty=True,
        retransmissions_cleared=True,
    )
    local_step = speaker.originate_router_lsa(
        "eth0",
        RouterLSA(
            header=LSAHeader("router", "1.1.1.1", "1.1.1.1", sequence=1),
            area_id="0.0.0.0",
            links=(LinkDescription(neighbor_router_id="2.2.2.2", metric=10),),
            stub_networks=(StubNetwork(prefix="10.0.1.0/24", metric=1),),
        )
    )
    remote_step = speaker.receive_router_lsa(
        "eth0",
        "2.2.2.2",
        RouterLSA(
            header=LSAHeader("router", "2.2.2.2", "2.2.2.2", sequence=1),
            area_id="0.0.0.0",
            links=(LinkDescription(neighbor_router_id="1.1.1.1", metric=10),),
            stub_networks=(StubNetwork(prefix="10.0.2.0/24", metric=2),),
        )
    )
    summary_step = speaker.summarize_to_area("0.0.0.0", "0.0.0.1")
    speaker.register_abr_cost("0.0.0.1", "1.1.1.1", 0)
    import_step = speaker.import_summaries("0.0.0.1", summary_step.summaries)

    print("dr:", election_step.election.designated_router if election_step.election else None)
    print("hello_state:", hello_step.neighbor_states["eth0:2.2.2.2"].value)
    print("exchange_state:", exchange_step.neighbor_states["eth0:2.2.2.2"].value)
    print("local_routes:", [route.prefix for route in local_step.routes])
    print("remote_routes:", [route.prefix for route in remote_step.routes])
    print("flooded_interfaces:", remote_step.flooded_interfaces)
    print("summary_prefixes:", [summary.prefix for summary in summary_step.summaries])
    print("imported_area_1:", [route.prefix for route in import_step.area_routes_by_area.get("0.0.0.1", ())])


if __name__ == "__main__":
    main()
