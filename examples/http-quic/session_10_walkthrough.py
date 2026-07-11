from protocol_in_code.http.server_loop import ToyHttpServer, handle_connection


def home() -> tuple[int, str, str | None]:
    return 200, "hello", "etag-1"


def main() -> None:
    print("Session 10 walkthrough: Build the toy HTTP server loop")
    print()

    # Two keep-alive requests followed by a close, all on one connection.
    server = ToyHttpServer(routes={"/": home})
    first_req = "GET / HTTP/1.1\r\nHost: example.com\r\nConnection: keep-alive\r\n\r\n"
    second_req = "GET / HTTP/1.1\r\nHost: example.com\r\nConnection: keep-alive\r\n\r\n"
    close_req = "GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n"
    responses = handle_connection(server, [first_req, second_req, close_req])
    marker = "OK" if [r.status for r in responses] == [200, 200, 200] and len(responses) == 3 else "NG"
    print(f"[{marker}] two keep-alive then close         -> statuses={[r.status for r in responses]}")

    marker = "OK" if server.trace[-1] == "connection-close" else "NG"
    print(f"[{marker}] trace shows the close              -> trace[-1]={server.trace[-1]!r}")

    # A request for a route that was never registered.
    server_404 = ToyHttpServer(routes={"/": home})
    not_found_req = "GET /missing HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n"
    responses_404 = handle_connection(server_404, [not_found_req])
    marker = "OK" if responses_404[0].status == 404 else "NG"
    print(f"[{marker}] unknown route                      -> status={responses_404[0].status}")

    # A malformed request line: the loop must stop, not skip and continue.
    server_bad = ToyHttpServer(routes={"/": home})
    garbage_req = "not a request at all"
    trailing_req = "GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"
    responses_bad = handle_connection(server_bad, [garbage_req, trailing_req])
    marker = "OK" if len(responses_bad) == 1 and responses_bad[0].status == 400 else "NG"
    print(f"[{marker}] garbage request -> 400, loop stops -> responses={[r.status for r in responses_bad]}")

    marker = "OK" if server_bad.trace[-1].startswith("400 parse:") else "NG"
    print(f"[{marker}] trace records the parse failure    -> trace[-1]={server_bad.trace[-1]!r}")

    # A request missing the required Host header on HTTP/1.1: 400, loop stops.
    server_headers = ToyHttpServer(routes={"/": home})
    missing_host_req = "GET / HTTP/1.1\r\n\r\n"
    responses_headers = handle_connection(server_headers, [missing_host_req])
    marker = "OK" if responses_headers[0].status == 400 and server_headers.trace[-1].startswith("400 headers:") else "NG"
    print(f"[{marker}] missing Host header -> 400         -> trace[-1]={server_headers.trace[-1]!r}")

    # Prime the cache with an etag, then revalidate on a second connection.
    server_cache = ToyHttpServer(routes={"/": home})
    prime_req = "GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n"
    handle_connection(server_cache, [prime_req])

    server_conditional = ToyHttpServer(routes={"/": home}, cached=dict(server_cache.cached))
    matching_req = (
        "GET / HTTP/1.1\r\nHost: example.com\r\nIf-None-Match: etag-1\r\nConnection: close\r\n\r\n"
    )
    responses_cond = handle_connection(server_conditional, [matching_req])
    marker = "OK" if responses_cond[0].status == 304 and responses_cond[0].body == "" else "NG"
    print(f"[{marker}] If-None-Match matches etag -> 304  -> status={responses_cond[0].status} body={responses_cond[0].body!r}")

    # A stale etag on the conditional request: server serves the fresh body again.
    server_changed = ToyHttpServer(routes={"/": home}, cached=dict(server_cache.cached))
    stale_req = (
        "GET / HTTP/1.1\r\nHost: example.com\r\nIf-None-Match: etag-old\r\nConnection: close\r\n\r\n"
    )
    responses_changed = handle_connection(server_changed, [stale_req])
    marker = "OK" if responses_changed[0].status == 200 else "NG"
    print(f"[{marker}] If-None-Match mismatch -> 200      -> status={responses_changed[0].status}")

    # A request list that runs out without any Connection: close.
    server_exhausted = ToyHttpServer(routes={"/": home})
    only_req = "GET / HTTP/1.1\r\nHost: example.com\r\nConnection: keep-alive\r\n\r\n"
    handle_connection(server_exhausted, [only_req])
    marker = "OK" if server_exhausted.trace[-1] == "requests-exhausted" else "NG"
    print(f"[{marker}] requests run out without close     -> trace[-1]={server_exhausted.trace[-1]!r}")

    marker = "OK" if len(server.trace) > 0 and len(server_bad.trace) > 0 else "NG"
    print(f"[{marker}] trace is non-empty on every server -> len={len(server.trace)},{len(server_bad.trace)}")


if __name__ == "__main__":
    main()
