from protocol_in_code.rpki.policy import PolicyAction, RoutingPolicy
from protocol_in_code.rpki.validate import OriginVerdict
from protocol_in_code.rpki.validator_loop import ToyValidator, demo_roas, evaluate_table


def main() -> None:
    print("Session 05 walkthrough: build the toy validator loop")
    print()

    policy = RoutingPolicy(reject_invalid=True, lower_pref_not_found=True)
    validator = ToyValidator(policy=policy)
    validator.load_roas(demo_roas())

    skip_lines = [line for line in validator.trace if "load: skipped" in line and "not-a-prefix" in line]
    marker = "OK" if len(skip_lines) == 1 else "NG"
    print(f"[{marker}] malformed ROA skipped at load -> {skip_lines[0] if skip_lines else '(missing)'}")

    valid = validator.check("192.0.2.0/24", 65001)
    marker = "OK" if valid.verdict is OriginVerdict.VALID and valid.action is PolicyAction.ACCEPT else "NG"
    print(f"[{marker}] VALID check     -> verdict={valid.verdict.value} action={valid.action.value}")

    invalid = validator.check("198.51.100.0/24", 65099)
    marker = "OK" if invalid.verdict is OriginVerdict.INVALID and invalid.action is PolicyAction.REJECT else "NG"
    print(f"[{marker}] INVALID check   -> verdict={invalid.verdict.value} action={invalid.action.value}")

    not_found = validator.check("203.0.114.0/24", 65003)
    marker = "OK" if not_found.verdict is OriginVerdict.NOT_FOUND and not_found.action is PolicyAction.ACCEPT_LOWER_PREF else "NG"
    print(f"[{marker}] NOT_FOUND check -> verdict={not_found.verdict.value} action={not_found.action.value}")

    absence_reason = [line for line in not_found.trace_slice if "absence of a ROA is not a denial" in line]
    marker = "OK" if absence_reason else "NG"
    print(f"[{marker}] absence is not denial -> {absence_reason[0] if absence_reason else '(missing)'}")

    announcements = (
        ("192.0.2.0/24", 65001),
        ("198.51.100.0/24", 65099),
        ("203.0.114.0/24", 65003),
        ("203.0.113.0/24", 65003),
    )
    report = evaluate_table(validator, announcements)
    expected_verdicts = {OriginVerdict.VALID: 2, OriginVerdict.INVALID: 1, OriginVerdict.NOT_FOUND: 1}
    marker = "OK" if report.total == 4 and report.verdict_counts == expected_verdicts else "NG"
    print(f"[{marker}] evaluate_table   -> total={report.total} verdict_counts={ {k.value: v for k, v in report.verdict_counts.items()} }")

    covering_line = [line for line in valid.trace_slice if "covering ROA(s)" in line]
    marker = "OK" if valid.trace_slice and covering_line else "NG"
    print(f"[{marker}] trace_slice non-empty, has covering-count line -> {covering_line[0] if covering_line else '(missing)'}")


if __name__ == "__main__":
    main()
