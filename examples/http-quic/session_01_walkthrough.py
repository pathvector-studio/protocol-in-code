from protocol_in_code.http.parse import ParseOutcome, parse_request


def main() -> None:
    print("Session 01 walkthrough: A request is parsed text")
    print()

    good = parse_request("GET /index.html HTTP/1.1\r\nHost: example.com\r\n\r\n")
    marker = "OK" if (
        good.outcome is ParseOutcome.OK
        and good.request is not None
        and good.request.method == "GET"
        and good.request.target == "/index.html"
        and good.request.version == "HTTP/1.1"
        and good.request.headers == (("Host", "example.com"),)
    ) else "NG"
    print(f"[{marker}] good GET request         -> {good.outcome.value}, fields intact")

    bad_request_line = parse_request("GET /index.html\r\nHost: example.com\r\n\r\n")
    marker = "OK" if bad_request_line.outcome is ParseOutcome.BAD_REQUEST_LINE else "NG"
    print(f"[{marker}] request line missing part -> {bad_request_line.outcome.value}")

    bad_header_line = parse_request("GET / HTTP/1.1\r\nHost example.com\r\n\r\n")
    marker = "OK" if bad_header_line.outcome is ParseOutcome.BAD_HEADER_LINE else "NG"
    print(f"[{marker}] header line has no colon  -> {bad_header_line.outcome.value}")

    unsupported_version = parse_request("GET / HTTP/0.9\r\nHost: example.com\r\n\r\n")
    marker = "OK" if unsupported_version.outcome is ParseOutcome.UNSUPPORTED_VERSION else "NG"
    print(f"[{marker}] HTTP/0.9 request line     -> {unsupported_version.outcome.value}")

    unsupported_version_2 = parse_request("GET / HTTP/2.0\r\nHost: example.com\r\n\r\n")
    marker = "OK" if unsupported_version_2.outcome is ParseOutcome.UNSUPPORTED_VERSION else "NG"
    print(f"[{marker}] HTTP/2.0 request line     -> {unsupported_version_2.outcome.value}")

    trailing_blanks = parse_request("GET / HTTP/1.1\r\nHost: example.com\r\n\r\n\r\n\r\n")
    marker = "OK" if (
        trailing_blanks.outcome is ParseOutcome.OK
        and trailing_blanks.request is not None
        and trailing_blanks.request.headers == (("Host", "example.com"),)
    ) else "NG"
    print(f"[{marker}] extra trailing blank lines -> {trailing_blanks.outcome.value}")

    no_headers = parse_request("GET / HTTP/1.1\r\n\r\n")
    marker = "OK" if (
        no_headers.outcome is ParseOutcome.OK
        and no_headers.request is not None
        and no_headers.request.headers == ()
    ) else "NG"
    print(f"[{marker}] request line, no headers  -> {no_headers.outcome.value}, headers=()")


if __name__ == "__main__":
    main()
