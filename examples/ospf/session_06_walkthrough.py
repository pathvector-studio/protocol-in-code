from protocol_in_code.ospf.lsa import LSAHeader, RouterLSA
from protocol_in_code.ospf.lsdb import LinkStateDatabase


def main() -> None:
    lsdb = LinkStateDatabase()
    older = RouterLSA(
        header=LSAHeader("router", "2.2.2.2", "2.2.2.2", sequence=10),
        area_id="0.0.0.0",
    )
    same = RouterLSA(
        header=LSAHeader("router", "2.2.2.2", "2.2.2.2", sequence=10, age=100),
        area_id="0.0.0.0",
    )
    newer = RouterLSA(
        header=LSAHeader("router", "2.2.2.2", "2.2.2.2", sequence=11),
        area_id="0.0.0.0",
    )

    print("install_old:", lsdb.install_router_lsa(older))
    print("install_same:", lsdb.install_router_lsa(same))
    print("install_new:", lsdb.install_router_lsa(newer))
    print("stored_sequence:", lsdb.router_lsas("0.0.0.0")[0].header.sequence)


if __name__ == "__main__":
    main()

