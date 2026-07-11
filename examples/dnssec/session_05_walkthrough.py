from protocol_in_code.dnssec.chain import ChainOutcome
from protocol_in_code.dnssec.validator_loop import (
    ToyValidatingResolver,
    build_demo_tree,
    format_trace,
    tamper_ds,
    tamper_record,
    unsign_child,
)


def main() -> None:
    print("Session 05 walkthrough: Build the toy validating resolver")
    print()

    tree = build_demo_tree()

    resolver = ToyValidatingResolver(zones=tree.zones, trust_anchor=tree.trust_anchor)
    report = resolver.resolve_and_validate("example.com", "A", tree.rrset, tree.rrsig)
    marker = "OK" if report.outcome is ChainOutcome.SECURE else "NG"
    print(f"[{marker}] example.com A, fresh resolver -> {report.outcome.value}")

    marker = "OK" if len(report.trace_slice) == 7 else "NG"
    print(f"[{marker}] SECURE trace is 7 lines        -> {len(report.trace_slice)} lines")

    marker = "OK" if report.trace_slice[-1] == ": KSK matches trust anchor" else "NG"
    print(f"[{marker}] last line is trust-anchor match -> {report.trace_slice[-1]!r}")

    rendered = format_trace(report)
    marker = "OK" if "com: key sig OK" in rendered and ": KSK matches trust anchor" in rendered else "NG"
    print(f"[{marker}] format_trace carries per-level lines")

    tampered_rrset = tamper_record(tree)
    record_resolver = ToyValidatingResolver(zones=tree.zones, trust_anchor=tree.trust_anchor)
    record_report = record_resolver.resolve_and_validate("example.com", "A", tampered_rrset, tree.rrsig)
    marker = "OK" if record_report.outcome is ChainOutcome.BOGUS_RECORD_SIG else "NG"
    print(f"[{marker}] tamper_record knob             -> {record_report.outcome.value}")

    ds_tree = tamper_ds(tree)
    ds_resolver = ToyValidatingResolver(zones=ds_tree.zones, trust_anchor=ds_tree.trust_anchor)
    ds_report = ds_resolver.resolve_and_validate("example.com", "A", ds_tree.rrset, ds_tree.rrsig)
    marker = "OK" if ds_report.outcome is ChainOutcome.BOGUS_DS_MISMATCH else "NG"
    print(f"[{marker}] tamper_ds knob                 -> {ds_report.outcome.value}")

    unsigned_tree = unsign_child(tree)
    unsigned_resolver = ToyValidatingResolver(zones=unsigned_tree.zones, trust_anchor=unsigned_tree.trust_anchor)
    unsigned_report = unsigned_resolver.resolve_and_validate("example.com", "A", unsigned_tree.rrset, unsigned_tree.rrsig)
    marker = "OK" if unsigned_report.outcome is ChainOutcome.INSECURE else "NG"
    print(f"[{marker}] unsign_child knob              -> {unsigned_report.outcome.value}")

    expired_resolver = ToyValidatingResolver(zones=tree.zones, trust_anchor=tree.trust_anchor)
    expired_resolver.tick(1_000_000)
    expired_report = expired_resolver.resolve_and_validate("example.com", "A", tree.rrset, tree.rrsig)
    marker = "OK" if expired_report.outcome is ChainOutcome.BOGUS_RECORD_SIG else "NG"
    print(f"[{marker}] clock past expiration          -> {expired_report.outcome.value}")

    marker = "OK" if "Expired" in expired_report.trace_slice[0] else "NG"
    print(f"[{marker}] expiry caught at leaf record sig -> {expired_report.trace_slice[0]!r}")

    mismatch_resolver = ToyValidatingResolver(zones=tree.zones, trust_anchor=tree.trust_anchor)
    mismatch_report = mismatch_resolver.resolve_and_validate("not-example.com", "A", tree.rrset, tree.rrsig)
    marker = "OK" if mismatch_report.outcome is ChainOutcome.BOGUS_RECORD_SIG else "NG"
    print(f"[{marker}] answer name != question name   -> {mismatch_report.outcome.value}")


if __name__ == "__main__":
    main()
