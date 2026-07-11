from protocol_in_code.dnssec.dnskey import KeyRole, derive_key_tag, key_rrset, make_key, sign_key_rrset
from protocol_in_code.dnssec.rrsig import Rrset, VerifyOutcome, sign_rrset, verify_rrsig


def main() -> None:
    print("Session 02 walkthrough: The key signs the key")
    print()

    zone = "example.com"
    ksk = make_key(zone, KeyRole.KSK, "ksk-secret-001")
    zsk = make_key(zone, KeyRole.ZSK, "zsk-secret-001")

    tag_again = derive_key_tag("ksk-secret-001")
    marker = "OK" if tag_again == ksk.key_tag else "NG"
    print(f"[{marker}] derive_key_tag is deterministic -> {tag_again} == {ksk.key_tag}")

    rrset = key_rrset(zone, (ksk, zsk))
    marker = "OK" if len(rrset.records) == 2 else "NG"
    print(f"[{marker}] key_rrset holds both keys       -> {rrset.records}")

    rrsig = sign_key_rrset((ksk, zsk), ksk, inception=100, expiration=200)

    verified_with_ksk = verify_rrsig(rrset, rrsig, ksk.key_secret, now=150)
    marker = "OK" if verified_with_ksk is VerifyOutcome.OK else "NG"
    print(f"[{marker}] DNSKEY rrset verifies with KSK  -> {verified_with_ksk.value}")

    verified_with_zsk = verify_rrsig(rrset, rrsig, zsk.key_secret, now=150)
    marker = "OK" if verified_with_zsk is VerifyOutcome.BAD_SIGNATURE else "NG"
    print(f"[{marker}] DNSKEY rrset fails with ZSK secret -> {verified_with_zsk.value}")

    a_rrset = Rrset(name=zone, rtype="A", records=("192.0.2.10",))
    a_rrsig = sign_rrset(a_rrset, zsk.key_secret, zsk.key_tag, signer=zone, inception=100, expiration=200)
    a_verified = verify_rrsig(a_rrset, a_rrsig, zsk.key_secret, now=150)
    marker = "OK" if a_verified is VerifyOutcome.OK else "NG"
    print(f"[{marker}] ordinary rrset verifies with ZSK -> {a_verified.value}")


if __name__ == "__main__":
    main()
