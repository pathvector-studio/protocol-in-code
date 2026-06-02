from protocol_in_code.bgp.ribs import (
    AdjRIBIn,
    AdjRIBOut,
    LocRIB,
    build_candidates,
    install_best_path,
    stage_advertisement,
    store_received_path,
)
from protocol_in_code.bgp.best_path import select_best_path
from protocol_in_code.bgp.update import PathAttributes


def main() -> None:
    adj_rib_in = AdjRIBIn()
    loc_rib = LocRIB()
    adj_rib_out = AdjRIBOut()

    store_received_path(
        adj_rib_in,
        peer_id="upstream-a",
        prefix="203.0.113.0/24",
        attributes=PathAttributes(
            next_hop="198.51.100.1",
            as_path=(64510, 64496),
            origin="igp",
            local_pref=100,
        ),
    )
    store_received_path(
        adj_rib_in,
        peer_id="upstream-b",
        prefix="203.0.113.0/24",
        attributes=PathAttributes(
            next_hop="198.51.100.2",
            as_path=(64520, 64530, 64496),
            origin="igp",
            local_pref=120,
        ),
    )

    candidates = build_candidates(adj_rib_in, "203.0.113.0/24")
    best = select_best_path(candidates)
    install_best_path(loc_rib, best)
    stage_advertisement(adj_rib_out, "customer-a", best)

    print("Session 06 walkthrough: Where routes live")
    print()
    print(f"adj_rib_in peers: {tuple(adj_rib_in.paths_by_peer.keys())}")
    print(f"candidates for 203.0.113.0/24: {len(candidates)}")
    print(f"loc_rib best next_hop: {loc_rib.best_paths['203.0.113.0/24'].next_hop}")
    print(
        "adj_rib_out customer-a prefixes: "
        f"{tuple(adj_rib_out.advertisements_by_peer['customer-a'].keys())}"
    )


if __name__ == "__main__":
    main()
