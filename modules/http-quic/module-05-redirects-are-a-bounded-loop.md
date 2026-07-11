# Session 05 / Module 05: Redirects Are a Bounded Loop

## Position

- Track: HTTP/QUIC
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/http-quic/module-05/index.html`
- Source file: `src/protocol_in_code/http/redirect.py`
- Walkthrough script: `examples/http-quic/session_05_walkthrough.py`

## Core Question

Following a redirect chain is a loop with no natural stopping point — what two mechanisms turn it into something that is guaranteed to terminate, and what determines whether a `POST` survives the trip?

## Outcome

By the end of this session, the learner should be able to:

- explain the two independent guards that bound a redirect chain (visited set, hop counter)
- state why the counter trips on the sixth redirect rather than the fifth
- explain which status codes rewrite `POST` to `GET` and which preserve the method
- distinguish `REDIRECT_LOOP` from `TOO_MANY_REDIRECTS` from `DEAD_END` by the exact condition that produces each

## Read Order

1. Read `RedirectOutcome`
2. Read `RedirectResult`
3. Read `_rewrite_method()`
4. Read `follow_redirects()`
5. Run `examples/http-quic/session_05_walkthrough.py`

## Read It Like Code

```python
RedirectResult(
    outcome,
    final_url,
    final_method,
    hops,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `outcome` | One of four terminal states; every call to `follow_redirects()` ends in exactly one. |
| `final_url` | Only populated on `RESOLVED`; every other outcome leaves it `None`. |
| `final_method` | The method as of the last rewrite, not necessarily the method the caller started with. |
| `hops` | Every URL visited, in order, including the starting URL and the one that ended the loop. |

## Decision Flow

```text
url already in visited          -> RedirectLoop        (cycle detected before any request)
url not in responses map        -> DeadEnd              (nothing there to answer)
status not in [300, 400)        -> Resolved             (a non-redirect response)
3xx with no Location            -> DeadEnd              (redirect with nowhere to go)
3xx with Location, loop continues, up to MAX_REDIRECTS + 1 iterations
loop exhausts iteration budget  -> TooManyRedirects
```

## Reading Lens

The important move in this session is to stop reading `follow_redirects()` as "keep following until it stops" and start asking, on every iteration:

- is this URL already in `visited`, checked before anything else happens to it?
- did the loop counter run out before the response even mattered?
- what was `current_method` the instant before this particular status code was applied?

## Toy Model Boundary

Real HTTP clients resolve `Location` against the current URL (relative references, scheme-relative references, and cross-origin implications for credentials and headers). This toy treats every key in `responses` as an already-absolute, already-final URL string — there is no relative-URL resolution and no cross-origin distinction. Redirect loop detection here is a single `visited` set of exact URL strings; real clients face subtleties like query-string variation that this toy does not model.

## Code Landmarks

### `MAX_REDIRECTS`

Set to 5. Read alongside the `for _ in range(MAX_REDIRECTS + 1)` loop in `follow_redirects()` — the range is deliberately one iteration wider than the constant name suggests.

### `_rewrite_method()`

Three branches, in this order: 303 always becomes GET; 307/308 always preserve the method; 301/302 rewrite only if the method is POST (everything else passes through). The docstring calls out that the 301/302 POST-to-GET rewrite is historical browser behavior, not something mandated by the original status-code semantics.

### `follow_redirects()` — the visited check

`if url in visited` runs at the top of every iteration, before the URL is added to `visited`, before `hops` is appended, and before the responses map is even consulted. A URL that reappears is caught immediately, without spending a "hop" on it.

### `follow_redirects()` — the DEAD_END branches

Two separate lines return `DEAD_END`: one when the URL is not a key in `responses` at all, and one when a 3xx response has `location is None`. Both are "nowhere to go," but they are reached from different states.

## Failure Questions

Use the source file to answer these:

1. `MAX_REDIRECTS` is 5, but the loop is `range(MAX_REDIRECTS + 1)`. Trace a chain of exactly 6 redirects (7 URLs) through the loop by hand — on which iteration does `TOO_MANY_REDIRECTS` actually get returned, and why does the constant's name not match the number of hops actually allowed?
2. `visited` is checked before `hops.append(url)` and before the response lookup. If the check happened after those two lines instead, what would change about the `hops` tuple returned for a self-redirecting URL?
3. A 302 response on a GET request never changes the method, but a 302 response on a POST request does. Read `_rewrite_method()` and state the exact condition that separates these two cases.
4. What is `final_method` for a chain that goes POST -> (303) -> GET -> (307) -> a 200 response? Walk each `_rewrite_method()` call in order.
5. Two different conditions both return `DEAD_END`. Name both, and describe a `responses` dict that would trigger the second one without ever triggering the first.

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/http-quic/session_05_walkthrough.py
```

The walkthrough resolves a 2-hop chain, shows 303 always producing GET while 307 preserves POST, shows 302 rewriting POST specifically, catches a self-loop, trips the 6-deep chain limit, and hits a dead end on a missing `Location` target.

## Done When

The learner can say all of the following without looking at notes:

- "Two independent guards bound the loop: a visited set for cycles, a fixed iteration count for long chains."
- "303 always becomes GET; 307 and 308 always preserve the method; 301 and 302 only rewrite POST."
- "REDIRECT_LOOP, TOO_MANY_REDIRECTS, and DEAD_END are three different failures reached by three different conditions, not one generic 'redirect failed.'"

## References

- RFC 9110 Section 15.4 (redirection 3xx status codes and method-preservation semantics)
