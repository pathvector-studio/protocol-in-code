from protocol_in_code.bgp.best_path import PathCandidate
from protocol_in_code.bgp.export_policy import ExportPolicy, PeerType
from protocol_in_code.bgp.export_refresh import ExportTarget, refresh_exports_for_prefix
from protocol_in_code.bgp.ribs import AdjRIBOut, LocRIB, install_best_path


def main() -> None:
    loc_rib = LocRIB()
    adj_rib_out = AdjRIBOut()
    customer = ExportTarget(
        peer_id="customer-1",
        peer_type=PeerType.EBGP,
        policy=ExportPolicy(local_as=64500, next_hop_self=True),
    )
    upstream = ExportTarget(
        peer_id="upstream-1",
        peer_type=PeerType.EBGP,
        policy=ExportPolicy(local_as=64500, deny_prefixes=("203.0.113.0/24",)),
    )

    install_best_path(
        loc_rib,
        PathCandidate(
            prefix="203.0.113.0/24",
            next_hop="198.51.100.1",
            local_pref=200,
            as_path=(64501, 64496),
        ),
    )
    first = refresh_exports_for_prefix("203.0.113.0/24", loc_rib, adj_rib_out, (customer, upstream))
    loc_rib.best_paths.pop("203.0.113.0/24", None)
    second = refresh_exports_for_prefix("203.0.113.0/24", loc_rib, adj_rib_out, (customer, upstream))

    print("first_change_kinds:", [change.kind.value for change in first])
    print("first_change_peers:", [change.peer_id for change in first])
    print("second_change_kinds:", [change.kind.value for change in second])
    print("adj_rib_out_after_withdraw:", adj_rib_out.advertisements_by_peer)


if __name__ == "__main__":
    main()
