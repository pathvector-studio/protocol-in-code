from protocol_in_code.ospf.lsa import LSAHeader, LinkDescription, RouterLSA
from protocol_in_code.ospf.lsdb import LinkStateDatabase
from protocol_in_code.ospf.spf import shortest_path_tree


def main() -> None:
    lsdb = LinkStateDatabase()
    lsas = (
        RouterLSA(
            header=LSAHeader("router", "1.1.1.1", "1.1.1.1", sequence=1),
            area_id="0.0.0.0",
            links=(
                LinkDescription(neighbor_router_id="2.2.2.2", metric=10),
                LinkDescription(neighbor_router_id="3.3.3.3", metric=30),
            ),
        ),
        RouterLSA(
            header=LSAHeader("router", "2.2.2.2", "2.2.2.2", sequence=1),
            area_id="0.0.0.0",
            links=(LinkDescription(neighbor_router_id="3.3.3.3", metric=5),),
        ),
        RouterLSA(
            header=LSAHeader("router", "3.3.3.3", "3.3.3.3", sequence=1),
            area_id="0.0.0.0",
        ),
    )
    for lsa in lsas:
        lsdb.install_router_lsa(lsa)
    tree = shortest_path_tree(lsdb.router_lsas("0.0.0.0"), root_router_id="1.1.1.1")

    print("order:", tree.order)
    print("cost_to_2:", tree.costs["2.2.2.2"])
    print("cost_to_3:", tree.costs["3.3.3.3"])
    print("parent_of_3:", tree.parents["3.3.3.3"])


if __name__ == "__main__":
    main()
