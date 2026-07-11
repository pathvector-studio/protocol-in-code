# Session 04 / Module 04: Cacheable Is a Decision Tree

## Position

- Track: HTTP/QUIC
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/http-quic/module-04/index.html`
- Source file: `src/protocol_in_code/http/caching.py`
- Walkthrough script: `examples/http-quic/session_04_walkthrough.py`

## Core Question

Given a response's caching directives, three separate questions have to be answered in order: should this be stored at all, can a stored copy be reused right now, and if not, does revalidation confirm nothing changed?

## Outcome

By the end of this session, the learner should be able to:

- state the one condition that overrides every other storage directive
- explain why a response with neither `max_age` nor `etag` is never stored, even without `no_store`
- trace `can_reuse()`'s branch order and say which check runs before which
- explain what a matching `etag` means for the response body, and what a non-matching one means

## Read Order

1. Read `ResponseDirectives` and `CachedResponse`
2. Read `can_store()`
3. Read `can_reuse()`
4. Read `revalidate()`
5. Run `examples/http-quic/session_04_walkthrough.py`

## Read It Like Code

```python
CachedResponse(
    stored_at,
    max_age,
    etag,
    no_store,
    no_cache,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `stored_at` | The `now` at which the entry entered the cache. Freshness is computed as `now - stored_at`, not tracked by a timer. |
| `max_age` | How long, in seconds, the entry is fresh from `stored_at`. On `CachedResponse` this is a plain `int` (already decided to be storable); on `ResponseDirectives` it is `int \| None` (may be entirely absent). |
| `etag` | If present, lets a stale entry be revalidated instead of re-fetched wholesale. If `None`, staleness has only one exit: `MUST_FETCH`. |
| `no_store` | Checked first, in `can_store()`. Overrides `max_age` even when `max_age` alone would otherwise make the response storable. |
| `no_cache` | Checked first, in `can_reuse()`. A stored entry can still exist with `no_cache=True` — it just can never be served without revalidating first. |

## Decision Flow

```text
can_store(directives):
    no_store is True                              -> DoNotStore
    max_age is None and etag is None               -> DoNotStore
    otherwise                                      -> Store

can_reuse(entry, now):
    entry.no_cache is True                         -> StaleMustRevalidate
    (now - entry.stored_at) < entry.max_age          -> Fresh
    entry.etag is not None                          -> StaleMustRevalidate
    otherwise                                      -> MustFetch

revalidate(entry, current_etag):
    entry.etag is not None and entry.etag == current_etag -> NotModified304
    otherwise                                              -> Changed200
```

## Reading Lens

The important move in this session is to stop thinking of "cacheable" as one yes/no property of a response and start asking:

- which of the three functions is being asked, and does the answer to one constrain what the others can even see? (an entry only reaches `can_reuse()` if `can_store()` already said `Store`)
- in `can_reuse()`, which check runs *first*, and does its answer short-circuit the rest — regardless of what `max_age` or `etag` say?
- does a `StaleMustRevalidate` verdict mean the entry is gone, or does it mean the entry is still there, just not servable without a round trip?

## Toy Model Boundary

RFC 9111 defines heuristic freshness (estimating a lifetime when no `max_age` or `Expires` is present, often from `Last-Modified`), the `Vary` header (multiple cached variants of the same URL keyed by request headers), and a considerably richer set of directives (`s-maxage`, `must-revalidate`, `stale-while-revalidate`, `private`/`public`, and more). None of that exists here: `can_store()` treats "no max_age and no etag" as unconditionally not-storable rather than falling back to a heuristic, there is exactly one cache entry shape with no variant dimension, and `RULES`-style directive combinations beyond `no_store`/`no_cache`/`max_age`/`etag` are out of scope. `revalidate()` only compares a single etag string; there is no `Last-Modified`/`If-Modified-Since` path at all.

## Code Landmarks

### `can_store()` — no_store wins over everything

```python
def can_store(response_directives: ResponseDirectives) -> StoreDecision:
    if response_directives.no_store:
        return StoreDecision.DO_NOT_STORE

    if response_directives.max_age is None and response_directives.etag is None:
        return StoreDecision.DO_NOT_STORE

    return StoreDecision.STORE
```

The `no_store` check runs first and returns immediately — a response with `no_store=True, max_age=3600` is still `DoNotStore`. A generous `max_age` never gets a chance to matter once `no_store` is set. The second check is a joint condition on *both* fields with `and`: either `max_age` or `etag` alone is enough to make a response storable, but both being absent is enough to reject it, even though `no_store` was never set.

### `can_reuse()` — order is the lesson

```python
def can_reuse(entry: CachedResponse, now: int) -> ReuseDecision:
    if entry.no_cache:
        return ReuseDecision.STALE_MUST_REVALIDATE

    age = now - entry.stored_at
    if age < entry.max_age:
        return ReuseDecision.FRESH

    if entry.etag is not None:
        return ReuseDecision.STALE_MUST_REVALIDATE

    return ReuseDecision.MUST_FETCH
```

`no_cache` is checked before age is even computed — an entry with `no_cache=True` and `age=0` (checked the instant it was stored) is still `StaleMustRevalidate`, never `Fresh`. The freshness comparison is strict `<`: at `age == entry.max_age` exactly, the entry has just become stale, not still fresh. Only after both of those checks fail does `etag` presence decide between a revalidatable stale entry and a hard miss.

### `revalidate()` — the only correctness axis is etag equality

```python
def revalidate(entry: CachedResponse, current_etag: str) -> RevalidationResult:
    if entry.etag is not None and entry.etag == current_etag:
        return RevalidationResult.NOT_MODIFIED_304
    return RevalidationResult.CHANGED_200
```

`entry.etag is not None` is checked explicitly even though `can_reuse()` only ever returns `STALE_MUST_REVALIDATE` via the `etag is not None` branch (or via `no_cache`, where `etag` could in principle be `None`) — `revalidate()` does not assume its caller already guaranteed a non-`None` etag; it re-checks. Any mismatch, including comparing against an entry with `etag=None`, falls through to `CHANGED_200`.

## Failure Questions

Use the source file to answer these:

1. A response has `no_store=True` and `max_age=3600`. What does `can_store()` return, and which `if` returns before the `max_age` value is ever inspected?
2. A response has `max_age=None` and `etag=None`, with `no_store=False`. What does `can_store()` return, and what is the reasoning behind rejecting it even though nothing was explicitly forbidden?
3. An entry has `no_cache=True`, `max_age=60`, `etag="v1"`, and is checked at `now == entry.stored_at` (age zero). What does `can_reuse()` return? Which check makes freshness irrelevant here?
4. An entry has `max_age=60`, `etag=None`. At `now = entry.stored_at + 60` exactly, what does `can_reuse()` return? Which of the two remaining checks after the age comparison decides, and why does the *absence* of an etag matter here specifically?
5. `revalidate()` is called with `entry.etag="v1"` and `current_etag="v1"`. What is returned? Now call it with the same entry but `current_etag="v2"`. What changes, and does `revalidate()` ever look at `max_age` or `stored_at` to decide?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/http-quic/session_04_walkthrough.py
```

The walkthrough shows `no_store` overriding a generous `max_age`, a response with nothing to key freshness on being rejected outright, an entry moving from `Fresh` to `StaleMustRevalidate` as `now` crosses `max_age`, the `etag`-absent case falling all the way to `MustFetch`, both `revalidate()` outcomes, and `no_cache` forcing revalidation even at age zero.

## Done When

The learner can say all of the following without looking at notes:

- "`no_store` is checked first in `can_store()` and overrides every other directive, including a present `max_age`."
- "A response with neither `max_age` nor `etag` is never stored — there being nothing to reuse it against is itself disqualifying."
- "In `can_reuse()`, `no_cache` is checked before age, age is checked with strict `<` against `max_age`, and only then does `etag` presence decide between revalidate and a hard fetch."

## References

- RFC 9111 Section 3 (Storing Responses in Caches)
- RFC 9111 Section 4 (Constructing Responses from Caches)
