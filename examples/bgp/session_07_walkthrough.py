from protocol_in_code.bgp.best_path import PathCandidate
from protocol_in_code.bgp.import_policy import ImportPolicy, apply_import_policy
from protocol_in_code.bgp.validation import ValidationState


def main() -> None:
    candidate = PathCandidate(
        prefix="203.0.113.0/24",
        next_hop="198.51.100.9",
        local_pref=100,
        as_path=(64510, 64496),
        origin_type=0,
    )

    scenarios = (
        (
            "raise local preference",
            ValidationState.VALID,
            ImportPolicy(local_pref_override=200),
        ),
        (
            "set vendor-local weight",
            ValidationState.VALID,
            ImportPolicy(weight=50),
        ),
        (
            "reject by next hop",
            ValidationState.VALID,
            ImportPolicy(reject_next_hops=("198.51.100.9",)),
        ),
        (
            "reject invalid before best path",
            ValidationState.INVALID,
            ImportPolicy(reject_invalid=True),
        ),
    )

    print("Session 07 walkthrough: Import policy rewrites inputs")
    print()
    for title, state, policy in scenarios:
        result = apply_import_policy(candidate, state, policy)
        print(f"- {title}")
        print(f"  validation_state: {state.value}")
        print(
            "  policy: "
            f"local_pref_override={policy.local_pref_override}, "
            f"weight={policy.weight}, "
            f"reject_next_hops={policy.reject_next_hops}, "
            f"reject_invalid={policy.reject_invalid}"
        )
        if result is None:
            print("  result: dropped before best-path")
        else:
            print(
                "  result: "
                f"local_pref={result.local_pref}, "
                f"weight={result.weight}, "
                f"next_hop={result.next_hop}"
            )
        print()


if __name__ == "__main__":
    main()
