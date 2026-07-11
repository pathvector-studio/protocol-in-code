from protocol_in_code.rpki.roa import Roa
from protocol_in_code.rpki.validate import OriginVerdict, validate_origin


def main() -> None:
    print("Session 03 walkthrough: Three verdicts, not two")
    print()

    valid_roas = (Roa(prefix="203.0.113.0/24", max_length=24, origin_asn=65001),)
    valid_result = validate_origin(valid_roas, "203.0.113.0/24", 65001)
    marker = "OK" if valid_result.verdict is OriginVerdict.VALID and valid_result.matched_roa is not None else "NG"
    print(f"[{marker}] covering roa, right asn    -> {valid_result.verdict.value} matched={valid_result.matched_roa}")

    specific_roas = (Roa(prefix="203.0.113.0/24", max_length=23, origin_asn=65001),)
    specific_result = validate_origin(specific_roas, "203.0.113.0/24", 65001)
    marker = "OK" if specific_result.verdict is OriginVerdict.INVALID and "/23" in specific_result.reason else "NG"
    print(f"[{marker}] too specific, max_length 23-> {specific_result.verdict.value} reason={specific_result.reason!r}")

    wrong_asn_roas = (Roa(prefix="203.0.113.0/24", max_length=24, origin_asn=65001),)
    wrong_asn_result = validate_origin(wrong_asn_roas, "203.0.113.0/24", 65099)
    marker = "OK" if wrong_asn_result.verdict is OriginVerdict.INVALID and "not AS" in wrong_asn_result.reason else "NG"
    print(f"[{marker}] covering roa, wrong asn    -> {wrong_asn_result.verdict.value} reason={wrong_asn_result.reason!r}")

    not_found_result = validate_origin((), "203.0.113.0/24", 65001)
    marker = "OK" if not_found_result.verdict is OriginVerdict.NOT_FOUND and "not a denial" in not_found_result.reason else "NG"
    print(f"[{marker}] no covering roa at all     -> {not_found_result.verdict.value} reason={not_found_result.reason!r}")

    announcement = ("203.0.113.0/24", 65001)
    verdicts = (
        validate_origin(valid_roas, *announcement),
        validate_origin(specific_roas, *announcement),
        validate_origin((), *announcement),
    )
    marker = "OK" if [v.verdict for v in verdicts] == [OriginVerdict.VALID, OriginVerdict.INVALID, OriginVerdict.NOT_FOUND] else "NG"
    print(f"[{marker}] same announcement, 3 roa sets -> {[v.verdict.value for v in verdicts]}")


if __name__ == "__main__":
    main()
