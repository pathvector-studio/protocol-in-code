from protocol_in_code.ospf.areas import import_summary_lsas
from protocol_in_code.ospf.flooding import InterfaceState
from protocol_in_code.ospf.hello import InterfaceHelloConfig, OSPFHelloPacket
from protocol_in_code.ospf.lsa import LSAHeader, LinkDescription, RouterLSA, StubNetwork
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
    speaker.receive_hello(
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
    speaker.complete_database_exchange("eth0", "2.2.2.2")
    speaker.originate_router_lsa(
        "eth0",
        RouterLSA(
            header=LSAHeader("router", "1.1.1.1", "1.1.1.1", sequence=1),
            area_id="0.0.0.0",
            links=(LinkDescription(neighbor_router_id="2.2.2.2", metric=10),),
            stub_networks=(StubNetwork(prefix="10.0.20.0/24", metric=1),),
        ),
    )
    speaker.receive_router_lsa(
        "eth0",
        "2.2.2.2",
        RouterLSA(
            header=LSAHeader("router", "2.2.2.2", "2.2.2.2", sequence=1),
            area_id="0.0.0.0",
            links=(LinkDescription(neighbor_router_id="1.1.1.1", metric=10),),
            stub_networks=(StubNetwork(prefix="10.0.21.0/24", metric=8),),
        ),
    )
    summary_step = speaker.summarize_to_area("0.0.0.0", "0.0.0.1")
    imported = import_summary_lsas("0.0.0.1", summary_step.summaries, {"1.1.1.1": 7})

    print("summary_prefixes:", [summary.prefix for summary in summary_step.summaries])
    print("imported_next_hops:", [route.next_hop_router_id for route in imported])
    print("imported_costs:", [route.total_cost for route in imported])


if __name__ == "__main__":
    main()
