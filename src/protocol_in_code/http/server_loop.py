from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from .caching import CachedResponse, RevalidationResult, revalidate
from .headers import check_headers, normalize_name
from .parse import ParseOutcome, Request, parse_request

# Build the toy HTTP server loop: parse -> check headers -> route -> respond, looping over
# a connection's requests until Connection: close (or the requests run out). This module
# integrates parse.py, headers.py, and caching.py's revalidate() for If-None-Match. It
# deliberately excludes pool.py, redirect.py, and chunked.py: those are client-side
# concerns (a server here never initiates a request, follows a redirect, or reads chunked
# request bodies), so they don't belong in a server's request/response loop.

Handler = Callable[[], tuple[int, str, str | None]]  # -> (status, body, etag or None)


@dataclass(frozen=True)
class Response:
    status: int
    headers: tuple[tuple[str, str], ...]
    body: str


@dataclass
class ToyHttpServer:
    routes: dict[str, Handler] = field(default_factory=dict)
    cached: dict[str, CachedResponse] = field(default_factory=dict)
    clock: int = 0
    trace: list[str] = field(default_factory=list)


def _find_header(request: Request, name: str) -> str | None:
    target = normalize_name(name)
    for header_name, value in request.headers:
        if normalize_name(header_name) == target:
            return value
    return None


def _connection_should_close(request: Request) -> bool:
    value = _find_header(request, "Connection")
    if value is not None:
        return value.strip().lower() == "close"
    # HTTP/1.0 defaults to close; HTTP/1.1 defaults to keep-alive.
    return request.version == "HTTP/1.0"


def _respond_to(server: ToyHttpServer, request: Request) -> Response:
    handler = server.routes.get(request.target)
    if handler is None:
        server.trace.append(f"404 {request.target}")
        return Response(404, (), "")

    if_none_match = _find_header(request, "If-None-Match")
    entry = server.cached.get(request.target)
    if if_none_match is not None and entry is not None:
        result = revalidate(entry, if_none_match)
        if result is RevalidationResult.NOT_MODIFIED_304:
            server.trace.append(f"304 {request.target}")
            return Response(304, (), "")
        server.trace.append(f"revalidate-changed {request.target}")

    status, body, etag = handler()
    headers: tuple[tuple[str, str], ...] = ()
    if etag is not None:
        headers = (("ETag", etag),)
        server.cached[request.target] = CachedResponse(
            stored_at=server.clock, max_age=0, etag=etag, no_store=False, no_cache=True
        )

    server.trace.append(f"{status} {request.target}")
    return Response(status, headers, body)


def handle_connection(server: ToyHttpServer, raw_requests: list[str]) -> tuple[Response, ...]:
    """The loop: parse, check headers, route, respond -- keep-alive continues it, close ends it."""
    responses: list[Response] = []

    for raw in raw_requests:
        parsed = parse_request(raw)
        if parsed.outcome is not ParseOutcome.OK or parsed.request is None:
            server.trace.append(f"400 parse:{parsed.outcome.value}")
            responses.append(Response(400, (), ""))
            break

        request = parsed.request
        issues = check_headers(request)
        if issues:
            server.trace.append(f"400 headers:{issues[0].problem.value}")
            responses.append(Response(400, (), ""))
            break

        responses.append(_respond_to(server, request))

        if _connection_should_close(request):
            server.trace.append("connection-close")
            break
    else:
        server.trace.append("requests-exhausted")

    return tuple(responses)


if __name__ == "__main__":
    def home() -> tuple[int, str, str | None]:
        return 200, "hello", "etag-1"

    server = ToyHttpServer(routes={"/": home})

    keep_alive_req = "GET / HTTP/1.1\r\nHost: example.com\r\nConnection: keep-alive\r\n\r\n"
    close_req = "GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n"

    responses = handle_connection(server, [keep_alive_req, close_req])
    assert [r.status for r in responses] == [200, 200]
    assert server.trace[-1] == "connection-close"

    # A second connection, this time presenting the etag we minted above: expect 304.
    server2 = ToyHttpServer(routes={"/": home}, cached=dict(server.cached))
    conditional_req = (
        "GET / HTTP/1.1\r\nHost: example.com\r\nIf-None-Match: etag-1\r\nConnection: close\r\n\r\n"
    )
    responses2 = handle_connection(server2, [conditional_req])
    assert responses2[0].status == 304

    bad_header_req = "GET / HTTP/1.1\r\n\r\n"  # missing required Host
    server3 = ToyHttpServer(routes={"/": home})
    responses3 = handle_connection(server3, [bad_header_req])
    assert responses3[0].status == 400

    not_found_req = "GET /missing HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n"
    server4 = ToyHttpServer(routes={"/": home})
    responses4 = handle_connection(server4, [not_found_req])
    assert responses4[0].status == 404

    print("trace:", server.trace)
    print("[OK] server_loop.py")
