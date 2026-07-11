from protocol_in_code.dnssec.dnskey import KeyRole, make_key
from protocol_in_code.dnssec.ds import make_ds, ds_matches


def main() -> None:
    print("Session 03 walkthrough: DS links child to parent")
    print()

    child_ksk = make_key("child.example.", KeyRole.KSK, "child-ksk-secret")
    ds = make_ds(child_ksk)

    matches_same_key = ds_matches(ds, child_ksk)
    marker = "OK" if matches_same_key else "NG"
    print(f"[{marker}] ds_matches the same KSK           -> {matches_same_key}")

    different_key = make_key("child.example.", KeyRole.KSK, "a-different-secret")
    matches_different_key = ds_matches(ds, different_key)
    marker = "OK" if not matches_different_key else "NG"
    print(f"[{marker}] ds rejects a different key         -> {matches_different_key}")

    same_secret_other_zone = make_key("other.example.", KeyRole.KSK, "child-ksk-secret")
    matches_other_zone = ds_matches(ds, same_secret_other_zone)
    marker = "OK" if not matches_other_zone else "NG"
    print(f"[{marker}] same secret, different zone rejected -> {matches_other_zone}")

    marker = "OK" if (ds.child_zone, ds.key_tag) == ("child.example.", child_ksk.key_tag) else "NG"
    print(f"[{marker}] Ds fields readable: zone + key_tag -> {ds.child_zone} {ds.key_tag}")

    marker = "OK" if isinstance(ds.digest, str) and len(ds.digest) == 64 else "NG"
    print(f"[{marker}] Ds.digest is a sha256 hexdigest    -> len={len(ds.digest)}")


if __name__ == "__main__":
    main()
