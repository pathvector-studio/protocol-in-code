from protocol_in_code.ospf.hello import InterfaceHelloConfig, OSPFHelloPacket, evaluate_hello
from protocol_in_code.ospf.neighbor import (
    AdjacencyInputs,
    NeighborState,
    advance_neighbor_state,
    advance_on_hello,
    inputs_from_hello,
)


def main() -> None:
    hello = evaluate_hello(
        InterfaceHelloConfig(
            local_router_id="1.1.1.1",
            area_id="0.0.0.0",
            netmask="255.255.255.0",
            hello_interval=10,
            dead_interval=40,
        ),
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
    passive = advance_on_hello(
        NeighborState.DOWN,
        hello_accepted=hello.accepted,
        saw_self=hello.saw_self,
        should_form_full_adjacency=False,
    )
    exstart = advance_on_hello(
        NeighborState.DOWN,
        hello_accepted=hello.accepted,
        saw_self=hello.saw_self,
        should_form_full_adjacency=True,
    )
    loading = advance_neighbor_state(
        exstart,
        inputs_from_hello(
            hello,
            should_form_full_adjacency=True,
            database_description_ok=True,
            request_list_empty=False,
        ),
    )
    full = advance_neighbor_state(
        NeighborState.EXSTART,
        AdjacencyInputs(
            hello_accepted=hello.accepted,
            saw_self=hello.saw_self,
            should_form_full_adjacency=True,
            database_description_ok=True,
            request_list_empty=True,
            retransmissions_cleared=True,
        ),
    )

    print("passive_state:", passive.value)
    print("exstart_state:", exstart.value)
    print("loading_state:", loading.value)
    print("full_state:", full.value)


if __name__ == "__main__":
    main()
