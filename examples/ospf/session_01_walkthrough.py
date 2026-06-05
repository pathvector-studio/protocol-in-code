from protocol_in_code.ospf.hello import InterfaceHelloConfig, OSPFHelloPacket, evaluate_hello


def main() -> None:
    config = InterfaceHelloConfig(
        local_router_id="1.1.1.1",
        area_id="0.0.0.0",
        netmask="255.255.255.0",
        hello_interval=10,
        dead_interval=40,
    )

    accepted = evaluate_hello(
        config,
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
    mismatch = evaluate_hello(
        config,
        OSPFHelloPacket(
            source_router_id="2.2.2.2",
            area_id="0.0.0.1",
            netmask="255.255.255.0",
            hello_interval=10,
            dead_interval=40,
            priority=1,
            designated_router=None,
            backup_designated_router=None,
            neighbors=(),
        ),
    )

    print("accepted:", accepted.accepted, accepted.saw_self)
    print("mismatch:", mismatch.accepted, mismatch.reasons)


if __name__ == "__main__":
    main()
