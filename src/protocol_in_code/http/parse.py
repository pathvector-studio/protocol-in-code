from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

SUPPORTED_VERSIONS = ("HTTP/1.0", "HTTP/1.1")


class ParseOutcome(str, Enum):
    OK = "Ok"
    BAD_REQUEST_LINE = "BadRequestLine"
    BAD_HEADER_LINE = "BadHeaderLine"
    UNSUPPORTED_VERSION = "UnsupportedVersion"


@dataclass(frozen=True)
class Request:
    method: str
    target: str
    version: str
    headers: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ParseResult:
    outcome: ParseOutcome
    request: Request | None


def _parse_request_line(line: str) -> tuple[str, str, str] | None:
    parts = line.split(" ")
    if len(parts) != 3:
        return None
    method, target, version = parts
    if not method or not target or not version:
        return None
    return method, target, version


def _parse_header_line(line: str) -> tuple[str, str] | None:
    if ":" not in line:
        return None
    name, _, value = line.partition(":")
    name = name.strip()
    value = value.strip()
    if not name:
        return None
    return name, value


def parse_request(raw: str) -> ParseResult:
    """Before any semantics, HTTP is just text with a shape: a request line, then header lines."""
    lines = raw.split("\r\n")
    # The header/body separator is a blank line, and split() adds a trailing empty
    # element after the final "\r\n": both show up as empty strings at the end.
    while lines and lines[-1] == "":
        lines = lines[:-1]

    if not lines:
        return ParseResult(ParseOutcome.BAD_REQUEST_LINE, None)

    request_line = _parse_request_line(lines[0])
    if request_line is None:
        return ParseResult(ParseOutcome.BAD_REQUEST_LINE, None)
    method, target, version = request_line

    if version not in SUPPORTED_VERSIONS:
        return ParseResult(ParseOutcome.UNSUPPORTED_VERSION, None)

    headers: list[tuple[str, str]] = []
    for line in lines[1:]:
        header = _parse_header_line(line)
        if header is None:
            return ParseResult(ParseOutcome.BAD_HEADER_LINE, None)
        headers.append(header)

    request = Request(method=method, target=target, version=version, headers=tuple(headers))
    return ParseResult(ParseOutcome.OK, request)


if __name__ == "__main__":
    ok = parse_request("GET /index.html HTTP/1.1\r\nHost: example.com\r\n\r\n")
    assert ok.outcome is ParseOutcome.OK
    assert ok.request is not None and ok.request.method == "GET"
    assert ok.request.headers == (("Host", "example.com"),)

    bad_line = parse_request("GET /index.html\r\nHost: example.com\r\n\r\n")
    assert bad_line.outcome is ParseOutcome.BAD_REQUEST_LINE

    bad_header = parse_request("GET / HTTP/1.1\r\nHost example.com\r\n\r\n")
    assert bad_header.outcome is ParseOutcome.BAD_HEADER_LINE

    unsupported = parse_request("GET / HTTP/2.0\r\nHost: example.com\r\n\r\n")
    assert unsupported.outcome is ParseOutcome.UNSUPPORTED_VERSION

    print("[OK] parse.py")
