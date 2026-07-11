from protocol_in_code.http.headers import HeaderIssue, HeaderProblem, check_headers, normalize_name
from protocol_in_code.http.parse import Request


def main() -> None:
    print("Session 02 walkthrough: Headers come with rules")
    print()

    clean = Request("GET", "/", "HTTP/1.1", (("Host", "example.com"),))
    issues = check_headers(clean)
    marker = "OK" if issues == () else "NG"
    print(f"[{marker}] clean 1.1 request         -> issues={issues}")

    missing_host = Request("GET", "/", "HTTP/1.1", ())
    issues = check_headers(missing_host)
    marker = "OK" if issues == (HeaderIssue("Host", HeaderProblem.MISSING_HOST),) else "NG"
    print(f"[{marker}] missing Host on 1.1       -> issues={issues}")

    duplicate_host = Request(
        "GET", "/", "HTTP/1.1", (("Host", "example.com"), ("Host", "other.com"))
    )
    issues = check_headers(duplicate_host)
    marker = "OK" if issues == (HeaderIssue("Host", HeaderProblem.DUPLICATE_HOST),) else "NG"
    print(f"[{marker}] duplicate Host             -> issues={issues}")

    bad_length = Request(
        "GET", "/", "HTTP/1.1", (("Host", "example.com"), ("Content-Length", "twelve"))
    )
    issues = check_headers(bad_length)
    marker = "OK" if issues == (
        HeaderIssue("Content-Length", HeaderProblem.INVALID_CONTENT_LENGTH),
    ) else "NG"
    print(f"[{marker}] non-digit Content-Length   -> issues={issues}")

    unknown_header = Request(
        "GET", "/", "HTTP/1.1", (("Host", "example.com"), ("X-Trace-Id", "abc123"))
    )
    issues = check_headers(unknown_header)
    marker = "OK" if issues == () else "NG"
    print(f"[{marker}] unknown header passes      -> issues={issues}")

    upper_host = Request("GET", "/", "HTTP/1.1", (("HOST", "example.com"),))
    issues = check_headers(upper_host)
    marker = "OK" if issues == () else "NG"
    print(f"[{marker}] HOST (uppercase) counts    -> issues={issues}")

    case_split_duplicate = Request(
        "GET", "/", "HTTP/1.1", (("Host", "example.com"), ("host", "other.com"))
    )
    issues = check_headers(case_split_duplicate)
    marker = "OK" if issues == (HeaderIssue("Host", HeaderProblem.DUPLICATE_HOST),) else "NG"
    print(f"[{marker}] Host + host is one field   -> issues={issues}")

    marker = "OK" if normalize_name(" HOST ") == normalize_name("host") == "host" else "NG"
    print(f"[{marker}] normalize_name folds case  -> {normalize_name(' HOST ')!r}")


if __name__ == "__main__":
    main()
