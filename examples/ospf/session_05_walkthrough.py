from protocol_in_code.ospf.flooding import FloodInterface, FloodDecision, InterfaceState, flood_lsa
from protocol_in_code.ospf.lsa import LSAHeader, RouterLSA


def main() -> None:
    current = RouterLSA(
        header=LSAHeader("router", "2.2.2.2", "2.2.2.2", sequence=10, age=30),
        area_id="0.0.0.0",
    )
    newer = RouterLSA(
        header=LSAHeader("router", "2.2.2.2", "2.2.2.2", sequence=11, age=5),
        area_id="0.0.0.0",
    )

    decision = flood_lsa(
        incoming_interface="eth0",
        interfaces=(
            FloodInterface(name="eth0", state=InterfaceState.FULL),
            FloodInterface(name="eth1", state=InterfaceState.FULL),
            FloodInterface(name="eth2", state=InterfaceState.EXCHANGE),
            FloodInterface(name="eth3", state=InterfaceState.WAITING),
        ),
        received_lsa=newer,
        current_lsa=current,
    )

    print("newer:", decision.newer)
    print("outgoing:", decision.outgoing_interfaces)


if __name__ == "__main__":
    main()

