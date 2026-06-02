from protocol_in_code.bgp.best_path import PathCandidate
from protocol_in_code.bgp.export_policy import ExportPolicy, PeerType, prepare_export


def main() -> None:
    installed = PathCandidate(
        prefix="203.0.113.0/24",
        next_hop="192.0.2.1",
        local_pref=200,
        as_path=(64496,),
        origin_type=0,
    )

    scenarios = (
        (
            "export to eBGP with local-as prepend",
            PeerType.EBGP,
            ExportPolicy(local_as=64500, next_hop_self=False, extra_prepend_count=1),
        ),
        (
            "export to iBGP with next-hop-self",
            PeerType.IBGP,
            ExportPolicy(local_as=64500, next_hop_self=True),
        ),
        (
            "deny prefix on export",
            PeerType.EBGP,
            ExportPolicy(local_as=64500, deny_prefixes=("203.0.113.0/24",)),
        ),
    )

    print("Session 08 walkthrough: Export policy decides what leaves")
    print()
    for title, peer_type, policy in scenarios:
        exported = prepare_export(installed, peer_type, policy)
        print(f"- {title}")
        print(f"  peer_type: {peer_type.value}")
        if exported is None:
            print("  result: not advertised")
        else:
            print(f"  next_hop: {exported.next_hop}")
            print(f"  as_path: {exported.as_path}")
        print()


if __name__ == "__main__":
    main()
