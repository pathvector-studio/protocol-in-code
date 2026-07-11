from protocol_in_code.tls.messages import ClientHello, HelloValidity, validate_client_hello


def main() -> None:
    print("Session 01 walkthrough: Hello lists everything you can do")
    print()

    full_hello = ClientHello(
        offered_versions=("TLS1.3", "TLS1.2"),
        cipher_suites=("TLS_AES_128_GCM_SHA256",),
        server_name="example.com",
        alpn=("h2", "http/1.1"),
        session_ticket="ticket-abc123",
    )
    result = validate_client_hello(full_hello)
    marker = "OK" if result is HelloValidity.VALID else "NG"
    print(f"[{marker}] fully populated hello        -> {result.value}")
    print(f"[OK] fields print as declared      -> versions={full_hello.offered_versions} "
          f"suites={full_hello.cipher_suites} sni={full_hello.server_name!r} "
          f"alpn={full_hello.alpn} ticket={full_hello.session_ticket!r}")

    bare_hello = ClientHello(
        offered_versions=("TLS1.3",),
        cipher_suites=("TLS_AES_128_GCM_SHA256",),
        server_name="example.com",
    )
    marker = "OK" if bare_hello.alpn == () else "NG"
    print(f"[{marker}] alpn defaults to empty tuple -> {bare_hello.alpn!r}")
    marker = "OK" if bare_hello.session_ticket is None else "NG"
    print(f"[{marker}] session_ticket defaults None -> {bare_hello.session_ticket!r}")

    no_versions = ClientHello(
        offered_versions=(),
        cipher_suites=("TLS_AES_128_GCM_SHA256",),
        server_name="example.com",
    )
    result = validate_client_hello(no_versions)
    marker = "OK" if result is HelloValidity.NO_VERSIONS else "NG"
    print(f"[{marker}] no offered versions          -> {result.value}")

    no_suites = ClientHello(
        offered_versions=("TLS1.3",),
        cipher_suites=(),
        server_name="example.com",
    )
    result = validate_client_hello(no_suites)
    marker = "OK" if result is HelloValidity.NO_CIPHER_SUITES else "NG"
    print(f"[{marker}] no cipher suites             -> {result.value}")

    empty_name = ClientHello(
        offered_versions=("TLS1.3",),
        cipher_suites=("TLS_AES_128_GCM_SHA256",),
        server_name="",
    )
    result = validate_client_hello(empty_name)
    marker = "OK" if result is HelloValidity.EMPTY_SERVER_NAME else "NG"
    print(f"[{marker}] empty server_name            -> {result.value}")


if __name__ == "__main__":
    main()
