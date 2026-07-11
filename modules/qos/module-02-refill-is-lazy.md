# Session 02 / Module 02: Refill Is Lazy

## Position

- Track: QoS
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/qos/module-02/index.html`
- Source file: `src/protocol_in_code/qos/refill.py`
- Walkthrough script: `examples/qos/session_02_walkthrough.py`

## Core Question

If nothing is ticking a clock in the background, when does a token bucket's balance actually get updated, and why is the math split into its own file with no bucket object in sight?

## Outcome

By the end of this session, the learner should be able to:

- compute `compute_refill()`'s result by hand for a given `tokens`, `rate_per_sec`, `last_refill_at`, and `now`
- explain why zero or negative elapsed time leaves the balance untouched
- explain why the growth is capped at `capacity`
- explain why this module takes plain scalars instead of a `TokenBucket`, and what that buys the codebase

## Read Order

1. Read the module docstring
2. Read `RefillResult`
3. Read `compute_refill()`
4. Read its docstring's two named branches
5. Run `examples/qos/session_02_walkthrough.py`

## Read It Like Code

```python
compute_refill(
    tokens,
    capacity,
    rate_per_sec,
    last_refill_at,
    now,
) -> RefillResult(tokens, last_refill_at)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `tokens` (input) | The balance as of `last_refill_at`. Not necessarily current — that's the whole point of this function. |
| `last_refill_at` (input) | The timestamp the input `tokens` value is anchored to. Elapsed time is computed relative to this, not to any absolute origin. |
| `now` (input) | The instant being asked about. Supplied by the caller, never read from a clock inside this function. |
| `RefillResult.tokens` | The caller's new balance, capped at `capacity`. |
| `RefillResult.last_refill_at` | Set to `now` only if a refill actually happened; otherwise left exactly where it was. |

## Decision Flow

```text
elapsed = now - last_refill_at
elapsed <= 0   -> untouched: return (tokens, last_refill_at) unchanged
elapsed > 0    -> grown = tokens + elapsed * rate_per_sec
                  capped = min(grown, capacity)
                  return (capped, now)
```

## Reading Lens

The important move in this session is to stop thinking of refill as something that "happens over time" and start asking:

- what is `elapsed` for this specific call, and is it positive, zero, or negative?
- did `last_refill_at` in the result actually change, or did this call return the input unchanged?
- could this function be called with a `TokenBucket` instance? Look at the signature — it can't. It never sees one.
- compare this to `dns/cache.py`'s `entry_is_expired()`. Neither file runs a background process. A cache entry doesn't quietly expire on a timer — it stays exactly as stored until the next `lookup()` call asks "given `now`, are you still good?" and does the arithmetic right then. `compute_refill()` is the same trick applied to a balance instead of a boolean: debt (unclaimed growth) accrues silently and is only ever settled the moment something calls this function with a `now`.

## Toy Model Boundary

Real rate limiters often use monotonic nanosecond clocks and track fractional accrual with higher precision than a simple `elapsed * rate_per_sec` multiply — some also handle clock skew or backwards-moving clocks defensively rather than just treating negative elapsed as zero growth. This lesson uses an integer `now` and trusts the caller not to go backwards in a way that matters.

There is no bucket object here at all, on purpose — see Code Landmarks. This file only ever computes a pair of numbers; it never stores anything or decides whether a request is allowed.

## Code Landmarks

### The module docstring's import-layout paragraph

Read this closely: `refill.py` has zero dependency on `token_bucket.py`. It takes `tokens`, `capacity`, `rate_per_sec`, `last_refill_at`, and `now` as plain scalars — not a `TokenBucket` object. `token_bucket.py` is the one that imports `compute_refill` from here and calls it inside `try_consume()`, then writes the two returned values back onto its own mutable dataclass fields (`bucket.tokens`, `bucket.last_refill_at`). This is a deliberate layout choice: refill is pure math with no side effects and no knowledge of what a "bucket" even is; the dataclass in `token_bucket.py` is just where that math's output gets stored. Grep for `TokenBucket` in this file — it does not appear.

### `compute_refill()`'s two named branches

The function docstring calls out exactly two branches worth remembering. First: `elapsed <= 0` (same instant, or `now` before `last_refill_at`) returns the input completely unchanged — no growth, no timestamp move. Second: the overflow cap — a long-idle bucket's `elapsed * rate_per_sec` can vastly exceed what the bucket can hold, and `min(grown, capacity)` clamps it. The docstring explicitly contrasts this with a leaky bucket's `level`, which never banks credit past a ceiling the same way (Session 03).

### `RefillResult` as a frozen pair

Both fields are returned together because they're always consistent with each other: if `tokens` changed, `last_refill_at` moved to `now` in the same result; if `tokens` didn't change, `last_refill_at` didn't either. There is no way to get a result with new tokens but a stale timestamp.

## Failure Questions

Use the source file to answer these:

1. `compute_refill(tokens=10, capacity=100, rate_per_sec=2, last_refill_at=5, now=5)` — what does `elapsed` equal, and what two fields of the result are guaranteed to match the input exactly?
2. Where exactly does the capacity cap get applied — before or after `elapsed * rate_per_sec` is added to `tokens`? What line proves it?
3. If `now` is less than `last_refill_at` (the clock appears to have gone backwards), does `compute_refill()` raise an error, or does it fall into the same branch as zero elapsed time? Which comparison in the code decides?
4. `compute_refill()`'s signature has no `TokenBucket` parameter. What would have to change about this function's signature if it needed to know a bucket's identity — and why does `try_consume()` in `token_bucket.py` not need to pass one in?
5. Two calls to `compute_refill()` with identical `tokens`, `capacity`, `rate_per_sec`, and `last_refill_at`, but different `now` values, are guaranteed to return the same `RefillResult` for the same `now` — why? What does this tell you about whether this function has any hidden state?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/qos/session_02_walkthrough.py
```

The walkthrough computes a plain elapsed-times-rate growth, shows zero elapsed time adding nothing, shows a negative-elapsed call also leaving the balance untouched, shows the capacity cap kicking in after a long idle period (both from an empty and a partial starting balance), and finally calls `compute_refill()` with nothing but scalars — no bucket object anywhere in sight — to make the purity of the function visible.

## Done When

The learner can say all of the following without looking at notes:

- "`compute_refill()` returns exactly `elapsed * rate_per_sec` added to the balance, capped at capacity — nothing more."
- "Refill only settles when something calls this function with a `now`; there is no background process accruing it in between."
- "This file takes scalars, not a `TokenBucket`, so it has zero dependency on the bucket module — the bucket is just where the answer gets stored."

## References

- RFC 2475 — An Architecture for Differentiated Services (general framing for traffic conditioning)
- RFC 2698 — A Two Rate Three Color Marker (trTCM), which builds token-bucket refill semantics into a two-rate metering scheme
