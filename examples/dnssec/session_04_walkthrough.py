from protocol_in_code.dnssec.chain import ChainOutcome, validate_chain
from protocol_in_code.dnssec.validator_loop import build_demo_tree, tamper_ds, tamper_record, unsign_child


def main() -> None:
    print("Session 04 walkthrough: Validation walks up the tree")
    print()

    tree = build_demo_tree()

    secure = validate_chain(tree.rrset, tree.rrsig, tree.zones, tree.trust_anchor, now=500)
    marker = "OK" if secure.outcome is ChainOutcome.SECURE else "NG"
    print(f"[{marker}] fully signed demo tree      -> {secure.outcome.value}")

    marker = "OK" if secure.trace[-1] == ': KSK matches trust anchor' else "NG"
    print(f"[{marker}] trace ends at trust anchor  -> {secure.trace[-1]!r}")

    bad_rrset = tamper_record(tree)
    record_bogus = validate_chain(bad_rrset, tree.rrsig, tree.zones, tree.trust_anchor, now=500)
    marker = "OK" if record_bogus.outcome is ChainOutcome.BOGUS_RECORD_SIG else "NG"
    print(f"[{marker}] answer swapped after signing -> {record_bogus.outcome.value}")

    ds_tree = tamper_ds(tree)
    ds_bogus = validate_chain(ds_tree.rrset, ds_tree.rrsig, ds_tree.zones, ds_tree.trust_anchor, now=500)
    marker = "OK" if ds_bogus.outcome is ChainOutcome.BOGUS_DS_MISMATCH else "NG"
    print(f"[{marker}] com's DS points at wrong key -> {ds_bogus.outcome.value}")

    unsigned_tree = unsign_child(tree)
    insecure = validate_chain(unsigned_tree.rrset, unsigned_tree.rrsig, unsigned_tree.zones, unsigned_tree.trust_anchor, now=500)
    marker = "OK" if insecure.outcome is ChainOutcome.INSECURE else "NG"
    print(f"[{marker}] com has no DS for example.com -> {insecure.outcome.value} (absent, not broken)")

    no_sig_failure = all("sig " not in line or " OK " in line for line in insecure.trace)
    marker = "OK" if no_sig_failure else "NG"
    print(f"[{marker}] INSECURE trace has no sig-failure line -> {insecure.trace}")


if __name__ == "__main__":
    main()
