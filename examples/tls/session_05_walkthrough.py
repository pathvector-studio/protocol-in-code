from protocol_in_code.tls.hostname import HostnameVerdict, match_hostname


def main() -> None:
    print("Session 05 walkthrough: A cert is for a name, not a server")
    print()

    exact = match_hostname("example.com", ("example.com",))
    marker = "OK" if exact.verdict is HostnameVerdict.MATCHED_EXACT else "NG"
    print(f"[{marker}] exact match                  -> {exact.verdict.value} {exact.matched_san!r}")

    case_insensitive = match_hostname("Example.COM", ("example.com",))
    marker = "OK" if case_insensitive.verdict is HostnameVerdict.MATCHED_EXACT else "NG"
    print(f"[{marker}] case-insensitive exact match -> {case_insensitive.verdict.value} {case_insensitive.matched_san!r}")

    wildcard = match_hostname("www.example.com", ("*.example.com",))
    marker = "OK" if wildcard.verdict is HostnameVerdict.MATCHED_WILDCARD else "NG"
    print(f"[{marker}] wildcard match                -> {wildcard.verdict.value} {wildcard.matched_san!r}")

    two_labels = match_hostname("a.b.example.com", ("*.example.com",))
    marker = "OK" if two_labels.verdict is HostnameVerdict.NO_MATCH else "NG"
    print(f"[{marker}] wildcard spans two labels    -> {two_labels.verdict.value}")

    bare_domain = match_hostname("example.com", ("*.example.com",))
    marker = "OK" if bare_domain.verdict is HostnameVerdict.NO_MATCH else "NG"
    print(f"[{marker}] wildcard vs bare domain      -> {bare_domain.verdict.value}")

    partial_label = match_hostname("www.example.com", ("w*.example.com",))
    marker = "OK" if partial_label.verdict is HostnameVerdict.NO_MATCH else "NG"
    print(f"[{marker}] partial-label wildcard       -> {partial_label.verdict.value}")

    no_match = match_hostname("example.org", ("example.com", "*.example.com"))
    marker = "OK" if no_match.verdict is HostnameVerdict.NO_MATCH and no_match.matched_san is None else "NG"
    print(f"[{marker}] no SAN owns the name         -> {no_match.verdict.value} {no_match.matched_san!r}")


if __name__ == "__main__":
    main()
