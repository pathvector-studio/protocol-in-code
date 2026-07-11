from protocol_in_code.tls.chain import Certificate, ChainVerdict, verify_chain


def main() -> None:
    print("Session 04 walkthrough: Trust is a walk up the chain")
    print()

    root = Certificate(
        subject="Root CA",
        issuer="Root CA",
        public_key_id="root-key",
        not_before=0,
        not_after=1000,
        is_ca=True,
    )
    intermediate = Certificate(
        subject="Intermediate CA",
        issuer="Root CA",
        public_key_id="intermediate-key",
        not_before=0,
        not_after=1000,
        is_ca=True,
    )
    leaf = Certificate(
        subject="example.com",
        issuer="Intermediate CA",
        public_key_id="leaf-key",
        not_before=0,
        not_after=1000,
        is_ca=False,
    )
    trust_store = {"Root CA": "root-key"}

    trusted = verify_chain((leaf, intermediate, root), trust_store, now=500)
    marker = "OK" if trusted is ChainVerdict.TRUSTED else "NG"
    print(f"[{marker}] leaf+intermediate+root chain -> {trusted.value}")

    wrong_issuer = Certificate(
        subject="example.com",
        issuer="Some Other CA",
        public_key_id="leaf-key",
        not_before=0,
        not_after=1000,
        is_ca=False,
    )
    broken = verify_chain((wrong_issuer, intermediate, root), trust_store, now=500)
    marker = "OK" if broken is ChainVerdict.BROKEN_CHAIN else "NG"
    print(f"[{marker}] issuer/subject mismatch      -> {broken.value}")

    expired = verify_chain((leaf, intermediate, root), trust_store, now=1000)
    marker = "OK" if expired is ChainVerdict.EXPIRED else "NG"
    print(f"[{marker}] now == leaf.not_after        -> {expired.value}")

    not_yet = verify_chain((leaf, intermediate, root), trust_store, now=-1)
    marker = "OK" if not_yet is ChainVerdict.NOT_YET_VALID else "NG"
    print(f"[{marker}] now before not_before        -> {not_yet.value}")

    untrusted_root = verify_chain((leaf, intermediate, root), {}, now=500)
    marker = "OK" if untrusted_root is ChainVerdict.UNTRUSTED_ROOT else "NG"
    print(f"[{marker}] root missing from trust store -> {untrusted_root.value}")

    empty = verify_chain((), trust_store, now=500)
    marker = "OK" if empty is ChainVerdict.EMPTY_CHAIN else "NG"
    print(f"[{marker}] empty chain                  -> {empty.value}")


if __name__ == "__main__":
    main()
