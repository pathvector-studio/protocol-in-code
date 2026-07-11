from protocol_in_code.rpki.roa import Roa, RoaValidity, validate_roa


def main() -> None:
    print("Session 01 walkthrough: A ROA is a permission slip")
    print()

    valid_roa = Roa(prefix="203.0.113.0/24", max_length=24, origin_asn=65001)
    valid_result = validate_roa(valid_roa)
    marker = "OK" if valid_result is RoaValidity.VALID else "NG"
    print(f"[{marker}] well-formed roa            -> {valid_result.value}")

    malformed_roa = Roa(prefix="not-a-prefix", max_length=24, origin_asn=65001)
    malformed_result = validate_roa(malformed_roa)
    marker = "OK" if malformed_result is RoaValidity.MALFORMED_PREFIX else "NG"
    print(f"[{marker}] unparseable prefix string  -> {malformed_result.value}")

    too_broad_roa = Roa(prefix="203.0.113.0/24", max_length=23, origin_asn=65001)
    too_broad_result = validate_roa(too_broad_roa)
    marker = "OK" if too_broad_result is RoaValidity.INVALID_MAX_LENGTH else "NG"
    print(f"[{marker}] max_length 23 on a /24     -> {too_broad_result.value}")

    over_ceiling_roa = Roa(prefix="203.0.113.0/24", max_length=33, origin_asn=65001)
    over_ceiling_result = validate_roa(over_ceiling_roa)
    marker = "OK" if over_ceiling_result is RoaValidity.INVALID_MAX_LENGTH else "NG"
    print(f"[{marker}] max_length 33 (past /32)   -> {over_ceiling_result.value}")

    printed = repr(valid_roa)
    fields_present = "prefix=" in printed and "max_length=" in printed and "origin_asn=" in printed
    marker = "OK" if fields_present else "NG"
    print(f"[{marker}] object prints readably     -> {printed}")


if __name__ == "__main__":
    main()
