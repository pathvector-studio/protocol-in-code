from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from .parse import Request


class HeaderProblem(str, Enum):
    INVALID_CONTENT_LENGTH = "InvalidContentLength"
    MISSING_HOST = "MissingHost"
    DUPLICATE_HOST = "DuplicateHost"
    INVALID_CONNECTION_VALUE = "InvalidConnectionValue"


@dataclass(frozen=True)
class HeaderIssue:
    name: str
    problem: HeaderProblem


def normalize_name(name: str) -> str:
    """Header names are case-insensitive: 'Host' and 'host' name the same field."""
    return name.strip().lower()


def _check_content_length(values: tuple[str, ...]) -> HeaderIssue | None:
    for value in values:
        if not value.isdigit():
            return HeaderIssue("Content-Length", HeaderProblem.INVALID_CONTENT_LENGTH)
    return None


def _check_host(values: tuple[str, ...]) -> HeaderIssue | None:
    if len(values) == 0:
        return HeaderIssue("Host", HeaderProblem.MISSING_HOST)
    if len(values) > 1:
        return HeaderIssue("Host", HeaderProblem.DUPLICATE_HOST)
    return None


def _check_connection(values: tuple[str, ...]) -> HeaderIssue | None:
    for value in values:
        if value.strip().lower() not in ("keep-alive", "close"):
            return HeaderIssue("Connection", HeaderProblem.INVALID_CONNECTION_VALUE)
    return None


# The rule table is the reading target: each known header maps to a small validator
# that receives every value seen for that header (headers may repeat) and returns
# an issue, or None if the values are fine. Unknown headers have no rule and pass.
RULES: dict[str, Callable[[tuple[str, ...]], HeaderIssue | None]] = {
    "content-length": _check_content_length,
    "host": _check_host,
    "connection": _check_connection,
}


def check_headers(request: Request) -> tuple[HeaderIssue, ...]:
    """Headers come with rules: run each known header's values through its rule."""
    by_name: dict[str, list[str]] = {}
    for name, value in request.headers:
        by_name.setdefault(normalize_name(name), []).append(value)

    # Host is required on HTTP/1.1 even when the header is absent entirely.
    if request.version == "HTTP/1.1" and "host" not in by_name:
        by_name["host"] = []

    issues: list[HeaderIssue] = []
    for name, values in by_name.items():
        rule = RULES.get(name)
        if rule is None:
            continue
        issue = rule(tuple(values))
        if issue is not None:
            issues.append(issue)

    return tuple(issues)


if __name__ == "__main__":
    assert normalize_name(" Host ") == "host"

    ok = Request("GET", "/", "HTTP/1.1", (("Host", "example.com"),))
    assert check_headers(ok) == ()

    duplicate_host = Request(
        "GET", "/", "HTTP/1.1", (("Host", "example.com"), ("Host", "other.com"))
    )
    issues = check_headers(duplicate_host)
    assert issues == (HeaderIssue("Host", HeaderProblem.DUPLICATE_HOST),)

    missing_host = Request("GET", "/", "HTTP/1.1", ())
    assert check_headers(missing_host) == (HeaderIssue("Host", HeaderProblem.MISSING_HOST),)

    bad_length = Request(
        "GET", "/", "HTTP/1.1", (("Host", "example.com"), ("Content-Length", "-1"))
    )
    assert check_headers(bad_length) == (
        HeaderIssue("Content-Length", HeaderProblem.INVALID_CONTENT_LENGTH),
    )

    print("[OK] headers.py")
