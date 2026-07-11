from protocol_in_code.dnssec.rrsig import Rrset, VerifyOutcome, sign_rrset, verify_rrsig


def main() -> None:
    print("Session 01 walkthrough: A signature rides beside the record")
    print()

    rrset = Rrset(name="example.com", rtype="A", records=("192.0.2.10",))
    key_secret = "zsk-secret-001"
    key_tag = 4242

    rrsig = sign_rrset(rrset, key_secret, key_tag, signer="example.com", inception=100, expiration=200)

    fresh = verify_rrsig(rrset, rrsig, key_secret, now=150)
    marker = "OK" if fresh is VerifyOutcome.OK else "NG"
    print(f"[{marker}] sign then verify inside window -> {fresh.value}")

    tampered = Rrset(name="example.com", rtype="A", records=("192.0.2.99",))
    bad_sig = verify_rrsig(tampered, rrsig, key_secret, now=150)
    marker = "OK" if bad_sig is VerifyOutcome.BAD_SIGNATURE else "NG"
    print(f"[{marker}] one record tampered           -> {bad_sig.value}")

    at_expiration = verify_rrsig(rrset, rrsig, key_secret, now=200)
    marker = "OK" if at_expiration is VerifyOutcome.EXPIRED else "NG"
    print(f"[{marker}] now == expiration exactly      -> {at_expiration.value}")

    before_inception = verify_rrsig(rrset, rrsig, key_secret, now=99)
    marker = "OK" if before_inception is VerifyOutcome.NOT_YET_VALID else "NG"
    print(f"[{marker}] now before inception           -> {before_inception.value}")

    wrong_name_rrset = Rrset(name="other.example.com", rtype="A", records=("192.0.2.10",))
    wrong_name = verify_rrsig(wrong_name_rrset, rrsig, key_secret, now=150)
    marker = "OK" if wrong_name is VerifyOutcome.WRONG_NAME else "NG"
    print(f"[{marker}] verified against a different name -> {wrong_name.value}")


if __name__ == "__main__":
    main()
