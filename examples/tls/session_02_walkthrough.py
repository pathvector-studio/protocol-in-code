from protocol_in_code.tls.negotiate import NegotiationOutcome, choose_alpn, choose_suite, choose_version


def main() -> None:
    print("Session 02 walkthrough: Agreement is a set intersection")
    print()

    # Client lists TLS1.2 first, TLS1.3 second - but the server prefers TLS1.3.
    # The SERVER's order wins, not the client's.
    client_versions = ("TLS1.2", "TLS1.3")
    server_versions = ("TLS1.3", "TLS1.2")
    result = choose_version(client_versions, server_versions)
    marker = "OK" if result.outcome is NegotiationOutcome.CHOSEN and result.chosen == "TLS1.3" else "NG"
    print(f"[{marker}] client prefers TLS1.2, server prefers TLS1.3 -> {result.outcome.value} {result.chosen}")

    version_mismatch = choose_version(("TLS1.0",), ("TLS1.3", "TLS1.2"))
    marker = "OK" if version_mismatch.outcome is NegotiationOutcome.NO_VERSION_OVERLAP else "NG"
    print(f"[{marker}] client only offers TLS1.0                    -> {version_mismatch.outcome.value}")

    # Client lists AES-256 first, server prefers CHACHA20 - server order still wins.
    client_suites = ("TLS_AES_256_GCM_SHA384", "TLS_CHACHA20_POLY1305_SHA256")
    server_suites = ("TLS_CHACHA20_POLY1305_SHA256", "TLS_AES_256_GCM_SHA384")
    suite_result = choose_suite(client_suites, server_suites)
    marker = "OK" if suite_result.outcome is NegotiationOutcome.CHOSEN and suite_result.chosen == "TLS_CHACHA20_POLY1305_SHA256" else "NG"
    print(f"[{marker}] client prefers AES-256, server prefers CHACHA20 -> {suite_result.outcome.value} {suite_result.chosen}")

    suite_mismatch = choose_suite(("TLS_AES_128_GCM_SHA256",), ("TLS_AES_256_GCM_SHA384",))
    marker = "OK" if suite_mismatch.outcome is NegotiationOutcome.NO_OVERLAP else "NG"
    print(f"[{marker}] no shared cipher suite                       -> {suite_mismatch.outcome.value}")

    # ALPN: client prefers http/1.1 first, server prefers h2 - server order wins again.
    alpn_result = choose_alpn(("http/1.1", "h2"), ("h2", "http/1.1"))
    marker = "OK" if alpn_result.outcome is NegotiationOutcome.CHOSEN and alpn_result.chosen == "h2" else "NG"
    print(f"[{marker}] client prefers http/1.1, server prefers h2   -> {alpn_result.outcome.value} {alpn_result.chosen}")

    alpn_no_overlap = choose_alpn(("http/1.1",), ("h2",))
    marker = "OK" if alpn_no_overlap.outcome is NegotiationOutcome.NO_OVERLAP else "NG"
    print(f"[{marker}] alpn offered but no shared protocol           -> {alpn_no_overlap.outcome.value}")

    alpn_empty = choose_alpn((), ("h2", "http/1.1"))
    marker = "OK" if alpn_empty.outcome is NegotiationOutcome.NO_OVERLAP and alpn_empty.chosen is None else "NG"
    print(f"[{marker}] client offers no alpn at all                  -> {alpn_empty.outcome.value} {alpn_empty.chosen}")


if __name__ == "__main__":
    main()
