from protocol_in_code.ospf.lsa import LSAHeader, LinkDescription, RouterLSA, StubNetwork
from protocol_in_code.ospf.lsdb import LinkStateDatabase
from protocol_in_code.ospf.recompute import apply_router_lsa


def main() -> None:
    lsdb = LinkStateDatabase()
    local = RouterLSA(
        header=LSAHeader("router", "1.1.1.1", "1.1.1.1", sequence=1),
        area_id="0.0.0.0",
        links=(LinkDescription(neighbor_router_id="2.2.2.2", metric=10),),
        stub_networks=(StubNetwork(prefix="10.0.1.0/24", metric=1),),
    )
    remote = RouterLSA(
        header=LSAHeader("router", "2.2.2.2", "2.2.2.2", sequence=1),
        area_id="0.0.0.0",
        links=(LinkDescription(neighbor_router_id="3.3.3.3", metric=5),),
        stub_networks=(StubNetwork(prefix="10.0.2.0/24", metric=2),),
    )
    changed_remote = RouterLSA(
        header=LSAHeader("router", "2.2.2.2", "2.2.2.2", sequence=2),
        area_id="0.0.0.0",
        links=(LinkDescription(neighbor_router_id="3.3.3.3", metric=5),),
        stub_networks=(StubNetwork(prefix="10.0.2.0/24", metric=20),),
    )

    apply_router_lsa(lsdb, "1.1.1.1", local)
    first = apply_router_lsa(lsdb, "1.1.1.1", remote)
    second = apply_router_lsa(lsdb, "1.1.1.1", changed_remote)

    print("first_changed:", first.changed_prefixes)
    print("first_cost:", first.routes_after[1].total_cost if len(first.routes_after) > 1 else None)
    print("second_changed:", second.changed_prefixes)
    print("second_cost:", second.routes_after[1].total_cost if len(second.routes_after) > 1 else None)


if __name__ == "__main__":
    main()
