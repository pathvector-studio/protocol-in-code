from protocol_in_code.bgp.policy import ValidationPolicy, decide_route_policy
from protocol_in_code.bgp.validation import ValidationState


def main() -> None:
    scenarios = (
        (
            "invalid with soft policy",
            ValidationState.INVALID,
            ValidationPolicy(reject_invalid=False, deprioritize_not_found=False),
        ),
        (
            "invalid with strict policy",
            ValidationState.INVALID,
            ValidationPolicy(reject_invalid=True, deprioritize_not_found=False),
        ),
        (
            "not_found with permissive policy",
            ValidationState.NOT_FOUND,
            ValidationPolicy(reject_invalid=True, deprioritize_not_found=False),
        ),
        (
            "not_found with cautious policy",
            ValidationState.NOT_FOUND,
            ValidationPolicy(reject_invalid=True, deprioritize_not_found=True),
        ),
        (
            "valid route",
            ValidationState.VALID,
            ValidationPolicy(reject_invalid=True, deprioritize_not_found=True),
        ),
    )

    print("Session 05 walkthrough: Validation state does not act by itself")
    print()
    for title, state, policy in scenarios:
        action = decide_route_policy(state, policy)
        print(f"- {title}")
        print(f"  validation_state: {state.value}")
        print(
            "  policy: "
            f"reject_invalid={policy.reject_invalid}, "
            f"deprioritize_not_found={policy.deprioritize_not_found}"
        )
        print(f"  action: {action.value}")
        print()


if __name__ == "__main__":
    main()
