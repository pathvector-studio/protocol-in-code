# Session 10 / Module 10: Build the Toy HTTP Server Loop

## Position

- Track: HTTP/QUIC
- Session: 10
- Site lesson: `pathvector-site/courses/protocols-in-code/http-quic/module-10/index.html`
- Source file: `src/protocol_in_code/http/server_loop.py`
- Walkthrough script: `examples/http-quic/session_10_walkthrough.py`

## Core Question

A server doesn't parse a request in isolation, or check headers in isolation, or answer from cache in isolation — it does all three, in order, once per request, for as many requests as one connection carries. What is the exact loop that wires those three earlier sessions together, and what makes it stop?

## Outcome

By the end of this session, the learner should be able to:

- name every earlier session that a piece of `handle_connection()` depends on, and what each contributes
- trace the per-request flow from raw text to `Response`, including both places a request can end the loop early
- explain the difference between HTTP/1.0 and HTTP/1.1's default `Connection` behavior, and where that default is decided
- explain why a `for...else` is the right tool for detecting "the requests ran out without a close"

## Read Order

1. Read the module comment above `Handler` (states the integration and the explicit scope exclusions)
2. Read `Response`
3. Read `ToyHttpServer`
4. Read `_find_header()`
5. Read `_connection_should_close()`
6. Read `_respond_to()`
7. Read `handle_connection()` — the reading target
8. Run `examples/http-quic/session_10_walkthrough.py`

## Read It Like Code

```python
ToyHttpServer(
    routes,   # dict[str, Handler]: path -> () -> (status, body, etag | None)
    cached,   # dict[str, CachedResponse]: path -> the etag-bearing entry last served
    clock,    # int: stamped onto CachedResponse.stored_at when a route is cached
    trace,    # list[str]: one entry per meaningful event, in order
)

Response(
    status,    # int
    headers,   # tuple[tuple[str, str], ...]
    body,      # str
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `ToyHttpServer.routes` | The only way a path resolves to behavior. A path not in this dict is always a 404, before anything else about the request is inspected. |
| `ToyHttpServer.cached` | Populated only when a handler returns a non-`None` etag. This is what makes `If-None-Match` revalidation possible on a later request. |
| `ToyHttpServer.trace` | The append-only record of what `handle_connection()` did. Every branch in this module appends exactly one line to it. |
| `Response.headers` | Empty on 400, 404, and 304 responses. Only a 200 with an etag ever populates it, and only with `ETag`. |

## Decision Flow

```text
handle_connection(server, raw_requests):
  for raw in raw_requests:
    1. parse_request(raw)
         not OK -> trace "400 parse:<outcome>", append 400 Response, BREAK
    2. check_headers(request)
         issues non-empty -> trace "400 headers:<problem>", append 400 Response, BREAK
    3. _respond_to(server, request):
         route not in server.routes                          -> trace "404 <path>", 404
         If-None-Match present AND cached entry present:
           revalidate() -> NOT_MODIFIED_304  -> trace "304 <path>", 304 (empty body)
           revalidate() -> CHANGED_200       -> trace "revalidate-changed <path>", fall through to handler
         otherwise -> call handler(), trace "<status> <path>", build Response
                       (if handler returned an etag: store it in server.cached)
    4. _connection_should_close(request)
         True  -> trace "connection-close", BREAK
         False -> continue to the next raw request
  else:
    (loop finished without ever BREAK-ing) -> trace "requests-exhausted"
  return tuple(responses)
```

## Reading Lens

The important move in this session is to stop reading `handle_connection()` as "a loop that calls three functions" and start asking, at every request:

- which of the three integrated modules — `parse.py`, `headers.py`, `caching.py` — is doing the work on this line, and what session taught it?
- is this request the one that ends the loop, and if so, by which of the two mechanisms — a 400 `break`, an explicit `Connection: close`, or simply running out of requests?
- what did `server.trace` gain as a result of this request, and would that one line tell a debugger what happened without looking at the response at all?

## Toy Model Boundary

`handle_connection()` takes `raw_requests: list[str]` — a connection here is a Python list of already-complete request strings, not a real socket, not real bytes, not a byte stream that could arrive in fragments. There is no I/O, no TCP underneath, no TLS, and single-threaded: one call, one connection, no concurrency.

The module's own docstring is explicit about what's excluded, and it's worth repeating exactly: `pool.py` (session 03), `redirect.py` (session 05), and `chunked.py` (session 06) are all client-side concerns — a server here never initiates a request, never follows a redirect, and never reads a chunked *request* body — so none of them belong in a server's request/response loop, and none of them are imported here.

## Parts List

Every non-stdlib import in `server_loop.py` was taught by an earlier session in this track. The capstone's only new code is `ToyHttpServer`, `Response`, and the loop that wires the imports together.

| Import | Session that taught it | What it contributes to `handle_connection()` |
|---|---|---|
| `parse.ParseOutcome`, `Request`, `parse_request` | 01 | Turns each raw request string into a `Request` or a `ParseOutcome` failure — the very first check in the loop body, and the only thing standing between raw text and everything else. |
| `headers.check_headers`, `normalize_name` | 02 | Validates the parsed `Request`'s headers (`Host`, `Content-Length`, `Connection`) against `headers.py`'s rule table; also backs `_find_header()`'s case-insensitive lookup used for both `Connection` and `If-None-Match`. |
| `caching.CachedResponse`, `RevalidationResult`, `revalidate` | 04 | `_respond_to()`'s `If-None-Match` branch: a cached entry plus a matching etag becomes a 304 via `revalidate()`, exactly as session 04 defined it. |

Sessions 03 (`pool.py`, keep-alive connection pooling), 05 (`redirect.py`, following redirects), and 06 (`chunked.py`, parsing a chunked body) are all client-side concerns and are deliberately not imported here — see Toy Model Boundary above.

Sessions 07 through 09 are the multiplexed-transport arc: session 07 (`h2_streams.py`) showed multiple HTTP/2 streams sharing one connection, and sessions 08–09 (this track's QUIC pair) showed the same multiplexing done per-stream at the transport layer, with independent flow control. `ToyHttpServer.handle_connection()` implements none of that — it serves exactly one request at a time, in sequence, over what session 03's pooling and sessions 07–09's multiplexing would otherwise let happen concurrently. This capstone closes the HTTP/1.1-style request/response loop; it does not attempt the multiplexed server those sessions point toward.

## Code Landmarks

### The module comment above `Handler`

States the integration in one sentence — parse, check headers, route, respond — and then states the scope exclusion just as plainly. Read this before the class definitions; it is the whole session's thesis statement.

### `_connection_should_close()`

```python
value = _find_header(request, "Connection")
if value is not None:
    return value.strip().lower() == "close"
return request.version == "HTTP/1.0"
```

Two defaults, one function. An explicit `Connection` header always wins; its absence falls back to the version-based default — HTTP/1.0 closes, HTTP/1.1 keeps the connection alive. `check_headers()` (session 02) has already rejected any `Connection` value other than `keep-alive` or `close` by the time this function runs, so the `== "close"` comparison is exhaustive in practice.

### `_respond_to()`'s `If-None-Match` branch

Revalidation only triggers when *both* an `If-None-Match` header and a `cached` entry for that path exist. A `CHANGED_200` result from `revalidate()` doesn't return early — it falls through to call the handler and build a normal response, just with a `revalidate-changed` trace entry instead of nothing.

### `handle_connection()`'s `for...else`

```python
for raw in raw_requests:
    ...
    if _connection_should_close(request):
        server.trace.append("connection-close")
        break
else:
    server.trace.append("requests-exhausted")
```

The `else` clause on a `for` loop runs only when the loop completes without hitting `break`. Every early exit in this loop — the two 400s and the explicit close — uses `break`, so `"requests-exhausted"` is only ever appended when every request in the list was handled and none of them asked to close the connection.

## Failure Questions

Use the source file to answer these:

1. When `parse_request()` fails inside `handle_connection()`, does the loop append to `responses`, to `server.trace`, or both — and in what order, relative to the `break`?
2. `_respond_to()` checks `if if_none_match is not None and entry is not None:` before calling `revalidate()`. If a request carries `If-None-Match` for a path that was never cached, which branch handles it, and what status code results?
3. `handle_connection()`'s `for...else` appends `"requests-exhausted"` only when the loop never `break`s. Construct the shortest `raw_requests` list (in terms of what each request's `Connection` header says) that would reach the `else` clause with more than zero responses.
4. `_connection_should_close()` returns `request.version == "HTTP/1.0"` when no `Connection` header is present. Is it possible for an HTTP/1.0 request to keep a connection alive through this function, and if so, how?
5. Only a `200` response from a handler that returns a non-`None` etag ever writes into `server.cached`. What happens to `server.cached` when a 304 is returned instead — does `_respond_to()` overwrite, delete, or leave the existing cached entry untouched?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/http-quic/session_10_walkthrough.py
```

The walkthrough drives one connection through two keep-alive requests followed by an explicit `Connection: close` and checks all three responses plus the trailing `connection-close` trace entry, requests an unregistered path and checks the 404, sends a syntactically invalid request and confirms the loop stops after exactly one 400 response with a `400 parse:` trace entry, sends a well-formed HTTP/1.1 request missing the required `Host` header and checks the `400 headers:` trace entry, primes the cache with an etag on one connection and then presents a matching `If-None-Match` on a second connection to get a 304 with an empty body, presents a stale `If-None-Match` value to confirm the server falls through to a fresh 200, and finally sends a single keep-alive request with no close and confirms the loop's `for...else` appends `"requests-exhausted"`.

## Done When

The learner can say all of the following without looking at notes:

- "handle_connection() is parse, then check headers, then route and possibly revalidate, then respond — repeated per request until something says stop."
- "A 400, from either parsing or header checks, breaks the loop immediately; nothing after it in raw_requests is ever touched."
- "requests-exhausted only appears when every request was handled and none of them, explicitly or by version default, asked to close the connection."

## References

- RFC 9112 Section 9 (Message Transport Requirements — connection persistence and closing)
- RFC 9110 Section 13 (Conditional Requests, including 304 Not Modified)
