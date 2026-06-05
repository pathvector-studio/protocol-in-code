from protocol_in_code.ospf.lsa import LSAHeader, LinkDescription, RouterLSA, StubNetwork
from protocol_in_code.ospf.routing import routes_from_tree
from protocol_in_code.ospf.spf import shortest_path_tree


def main() -> None:
    lsas = (
        RouterLSA(
            header=LSAHeader("router", "1.1.1.1", "1.1.1.1", sequence=1),
            area_id="0.0.0.0",
            links=(LinkDescription(neighbor_router_id="2.2.2.2", metric=10),),
            stub_networks=(StubNetwork(prefix="10.0.1.0/24", metric=1),),
        ),
        RouterLSA(
            header=LSAHeader("router", "2.2.2.2", "2.2.2.2", sequence=1),
            area_id="0.0.0.0",
            stub_networks=(StubNetwork(prefix="10.0.2.0/24", metric=3),),
        ),
    )
    tree = shortest_path_tree(lsas, root_router_id="1.1.1.1")
    routes = routes_from_tree("1.1.1.1", tree, lsas)

    for route in routes:
        print(route.prefix, route.next_hop_router_id, route.total_cost)


if __name__ == "__main__":
    main()

