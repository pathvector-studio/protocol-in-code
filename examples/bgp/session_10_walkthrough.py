from protocol_in_code.bgp.export_policy import ExportPolicy, PeerType
from protocol_in_code.bgp.import_policy import ImportPolicy
from protocol_in_code.bgp.pipeline import PipelinePolicies, process_single_route
from protocol_in_code.bgp.policy import ValidationPolicy
from protocol_in_code.bgp.ribs import AdjRIBIn, AdjRIBOut, LocRIB
from protocol_in_code.bgp.update import PathAttributes
from protocol_in_code.bgp.validation import VRP


def main() -> None:
    policies = PipelinePolicies(
        import_policy=ImportPolicy(local_pref_override=180),
        validation_policy=ValidationPolicy(reject_invalid=False, deprioritize_not_found=True),
        export_policy=ExportPolicy(local_as=64500, next_hop_self=True),
    )

    result = process_single_route(
        peer_id="upstream-a",
        prefix="203.0.113.0/24",
        attributes=PathAttributes(
            next_hop="198.51.100.1",
            as_path=(64496,),
            origin="igp",
            local_pref=100,
        ),
        vrps=[VRP(prefix="203.0.113.0/24", max_length=24, origin_as=64496)],
        policies=policies,
        adj_rib_in=AdjRIBIn(),
        loc_rib=LocRIB(),
        adj_rib_out=AdjRIBOut(),
        export_peer_id="customer-a",
        export_peer_type=PeerType.EBGP,
    )

    print("Session 10 walkthrough: One route through the whole pipeline")
    print()
    print(f"validation_state: {result.validation_state.value}")
    print(f"action: {result.action.value}")
    print(
        "installed_path: "
        f"{None if result.installed_path is None else result.installed_path.local_pref}"
    )
    print(
        "exported_as_path: "
        f"{None if result.exported_path is None else result.exported_path.as_path}"
    )


if __name__ == "__main__":
    main()
