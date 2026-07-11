from protocol_in_code.rpki.policy import PolicyAction, RoutingPolicy, apply_policy
from protocol_in_code.rpki.validate import OriginVerdict


def main() -> None:
    print("Session 04 walkthrough: policy decides what a verdict means")
    print()

    strict = RoutingPolicy(reject_invalid=True, lower_pref_not_found=True)
    permissive = RoutingPolicy(reject_invalid=False, lower_pref_not_found=False)

    valid_strict = apply_policy(OriginVerdict.VALID, strict)
    valid_permissive = apply_policy(OriginVerdict.VALID, permissive)
    marker = "OK" if valid_strict.action is PolicyAction.ACCEPT and valid_permissive.action is PolicyAction.ACCEPT else "NG"
    print(f"[{marker}] VALID     strict={valid_strict.action.value:18} permissive={valid_permissive.action.value:18} -> VALID is always ACCEPT")

    invalid_strict = apply_policy(OriginVerdict.INVALID, strict)
    invalid_permissive = apply_policy(OriginVerdict.INVALID, permissive)
    marker = (
        "OK"
        if invalid_strict.action is PolicyAction.REJECT and invalid_permissive.action is PolicyAction.ACCEPT_LOWER_PREF
        else "NG"
    )
    print(f"[{marker}] INVALID   strict={invalid_strict.action.value:18} permissive={invalid_permissive.action.value:18} -> same verdict, different policy, different fate")

    not_found_strict = apply_policy(OriginVerdict.NOT_FOUND, strict)
    not_found_permissive = apply_policy(OriginVerdict.NOT_FOUND, permissive)
    marker = (
        "OK"
        if not_found_strict.action is PolicyAction.ACCEPT_LOWER_PREF and not_found_permissive.action is PolicyAction.ACCEPT
        else "NG"
    )
    print(f"[{marker}] NOT_FOUND strict={not_found_strict.action.value:18} permissive={not_found_permissive.action.value:18} -> absence of a ROA is not a denial")


if __name__ == "__main__":
    main()
