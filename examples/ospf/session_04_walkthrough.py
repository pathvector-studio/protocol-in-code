from protocol_in_code.ospf.lsa import LSAHeader, LinkDescription, RouterLSA, StubNetwork, router_lsa_key


def main() -> None:
    lsa = RouterLSA(
        header=LSAHeader(
            lsa_type="router",
            lsa_id="1.1.1.1",
            advertising_router="1.1.1.1",
            sequence=10,
        ),
        area_id="0.0.0.0",
        links=(LinkDescription(neighbor_router_id="2.2.2.2", metric=10),),
        stub_networks=(StubNetwork(prefix="10.0.1.0/24", metric=1),),
    )

    print("lsa_key:", router_lsa_key(lsa))
    print("link_count:", len(lsa.links))
    print("stub_prefix:", lsa.stub_networks[0].prefix)


if __name__ == "__main__":
    main()

