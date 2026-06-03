from protocol_in_code.bgp.decision_process import evaluate_prefix_candidates, select_best_installable_for_prefix
from protocol_in_code.bgp.export_policy import ExportPolicy
from protocol_in_code.bgp.import_policy import ImportPolicy
from protocol_in_code.bgp.pipeline import PipelinePolicies
from protocol_in_code.bgp.policy import ValidationPolicy
from protocol_in_code.bgp.ribs import AdjRIBIn, store_received_path
from protocol_in_code.bgp.update import PathAttributes
from protocol_in_code.bgp.validation import VRP


def main() -> None:
    adj_rib_in = AdjRIBIn()
    store_received_path(
        adj_rib_in,
        "upstream-a",
        "203.0.113.0/24",
        PathAttributes(
            next_hop="198.51.100.1",
            local_pref=130,
            as_path=(64501, 64555),
            origin="igp",
        ),
    )
    store_received_path(
        adj_rib_in,
        "upstream-b",
        "203.0.113.0/24",
        PathAttributes(
            next_hop="198.51.100.2",
            local_pref=100,
            as_path=(64502, 64496),
            origin="igp",
        ),
    )
    vrps = [VRP(prefix="203.0.113.0/24", max_length=24, origin_as=64496)]
    policies = PipelinePolicies(
        import_policy=ImportPolicy(),
        validation_policy=ValidationPolicy(reject_invalid=False),
        export_policy=ExportPolicy(local_as=64500),
    )

    decisions = evaluate_prefix_candidates(adj_rib_in, "203.0.113.0/24", vrps, policies)
    best = select_best_installable_for_prefix(adj_rib_in, "203.0.113.0/24", vrps, policies)

    print("decisions:", [(decision.peer_id, decision.action.value, None if decision.installed_candidate is None else decision.installed_candidate.local_pref) for decision in decisions])
    print("best_next_hop:", best.next_hop if best else None)
    print("best_local_pref:", best.local_pref if best else None)


if __name__ == "__main__":
    main()
