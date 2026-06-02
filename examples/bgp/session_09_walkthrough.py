from protocol_in_code.bgp.recompute import handle_peer_loss
from protocol_in_code.bgp.ribs import AdjRIBIn, LocRIB, install_best_path, store_received_path
from protocol_in_code.bgp.best_path import select_best_path
from protocol_in_code.bgp.update import PathAttributes
from protocol_in_code.bgp.ribs import build_candidates


def main() -> None:
    adj_rib_in = AdjRIBIn()
    loc_rib = LocRIB()

    store_received_path(
        adj_rib_in,
        peer_id="upstream-a",
        prefix="203.0.113.0/24",
        attributes=PathAttributes(
            next_hop="198.51.100.1",
            as_path=(64510, 64496),
            origin="igp",
            local_pref=200,
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
            local_pref=100,
        ),
    )

    install_best_path(loc_rib, select_best_path(build_candidates(adj_rib_in, "203.0.113.0/24")))

    print("Session 09 walkthrough: Session loss and recompute")
    print()
    print(f"before loss best next_hop: {loc_rib.best_paths['203.0.113.0/24'].next_hop}")

    results = handle_peer_loss(adj_rib_in, loc_rib, peer_id="upstream-a")
    recomputed = results["203.0.113.0/24"]

    print("peer lost: upstream-a")
    if recomputed is None:
        print("after loss: prefix removed from loc_rib")
    else:
        print(f"after loss best next_hop: {recomputed.next_hop}")
        print(f"remaining peers: {tuple(adj_rib_in.paths_by_peer.keys())}")


if __name__ == "__main__":
    main()
