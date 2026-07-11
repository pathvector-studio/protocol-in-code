# Session 03 / Module 03: Leaky and Token Are Cousins

## Position

- Track: QoS
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/qos/module-03/index.html`
- Source file: `src/protocol_in_code/qos/leaky_bucket.py`
- Walkthrough script: `examples/qos/session_03_walkthrough.py`

## Core Question

A leaky bucket uses the same two variables and the same lazy-settlement trick as a token bucket — so why does an identical burst that a token bucket allows outright get dropped by a leaky bucket?

## Outcome

By the end of this session, the learner should be able to:

- name the two fields that fully determine a leaky bucket's behavior, and map them onto their token-bucket counterparts
- explain why arrivals add to `level` while a token bucket's consume subtracts from `tokens`
- explain why `offer()` drops the excess instead of queueing it
- state, with a concrete example, why a token bucket permits a capacity-sized burst while a leaky bucket at the same capacity overflows on it

## Read Order

1. Read the module docstring, especially the comparison table
2. Read `OfferOutcome`
3. Read `LeakyBucket`
4. Read `OfferResult`
5. Read `leak()`
6. Read `offer()`
7. Run `examples/qos/session_03_walkthrough.py`

## Read It Like Code

```python
LeakyBucket(
    capacity,
    level,
    leak_per_sec,
    last_leak_at,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `capacity` | The ceiling on backlog. `offer()` rejects anything that would push `level` past this. |
| `level` | How much backlog is waiting to drain right now — the mirror of a token bucket's `tokens`, but arrivals move it the opposite direction. |
| `leak_per_sec` | How fast backlog drains on its own, purely from elapsed time — the mirror of `rate_per_sec`. |
| `last_leak_at` | When `level` was last brought up to date. Same role as `last_refill_at` in Session 02, run in reverse. |

## Decision Flow

```text
offer(bucket, n, now):
  leak bucket up to `now` first           -> level may shrink, last_leak_at moves to now
  level + n > capacity                    -> Overflowed (level unchanged after leak, n dropped)
  otherwise                               -> Accepted (n added to level)
```

## Reading Lens

The important move in this session is to stop reading `leaky_bucket.py` as a new mechanism and start reading it as `token_bucket.py` with two signs flipped:

- where does this file's arrival logic ADD, and where does the token bucket's consume logic SUBTRACT?
- where does time SUBTRACT (leak) here, versus ADD (refill) in Session 02?
- when `offer()` rejects a request, what happens to `bucket.level`? Compare to what happens to `bucket.tokens` when `try_consume()` throttles.
- run the side-by-side scenario in the walkthrough: same `capacity`, same burst size `n`, same `now`. A token bucket that starts full allows the whole burst instantly. A leaky bucket that starts full (`level == capacity`, nothing drained yet) overflows on the identical burst. Both buckets have "two variables and a lazy settlement trick" — the difference is only in which direction is empty at capacity and which direction the request pushes.

## Toy Model Boundary

Real leaky-bucket shapers usually sit in front of an actual packet queue and emit queued packets at `leak_per_sec`, delaying traffic to smooth it rather than dropping every unit that doesn't fit right now. This lesson's `offer()` only ever returns `Accepted` or `Overflowed` — there is no queue, so anything that doesn't fit is dropped outright, not delayed and retried later.

`level` and `leak_per_sec` are floats settled with an integer `now`, same as `tokens` and `rate_per_sec` in Sessions 01 and 02. Real shapers typically run on nanosecond or microsecond clocks and track fractional leakage far more precisely.

## Code Landmarks

### The module docstring's comparison table

Read this table before the code. It states the whole session in ten lines: tokens start full and drain on use, level starts empty and fills on arrival; time adds tokens back but subtracts (leaks) the level; a token-bucket burst up to capacity passes at once, a leaky-bucket burst is smoothed to `leak_per_sec` worth of new room per second; token-bucket rejection means insufficient balance, leaky-bucket rejection means the backlog is already too full. Same skeleton, opposite temperament.

### `leak()` as the mirror of `compute_refill()`

`leak()` is `compute_refill()`'s sibling: `elapsed = now - bucket.last_leak_at`, same zero-or-negative-elapsed early return, but where refill computes `tokens + elapsed * rate_per_sec` capped at `capacity` from above, `leak()` computes `level - elapsed * leak_per_sec` floored at `0` from below. One caps growth at a ceiling; the other floors decay at zero. Note that `leak()` mutates `bucket` directly and takes a `LeakyBucket`, unlike `compute_refill()` which takes scalars — this file did not split its math out into a standalone function the way Session 02 did.

### `offer()`'s leak-then-check order

Same pattern as `try_consume()`: settle time first (`leak(bucket, now)`), then make the accept/reject decision against the now-current `level`. This is why a request that would overflow right now can be accepted a moment later purely from elapsed time — no separate "drain tick" needs to run.

### The docstring's closing burst comparison

The module docstring's own `if __name__ == "__main__"` block ends with the exact scenario this session is built around: a `TokenBucket` and a `LeakyBucket`, same `capacity=10`, both starting "full" in their own sense, offered the identical burst of size 10 at the identical `now=0`. The token bucket's `try_consume()` allows it outright. The leaky bucket's `offer()` overflows on it. Same two variables, same lazy-settlement idiom, opposite verdict.

## Failure Questions

Use the source file to answer these:

1. A fresh `LeakyBucket(capacity=10, level=0, ...)` receives an `offer()` for 6 units, then immediately (`now` unchanged) receives another `offer()` for 6 units. Why does the second call overflow even though `6 + 6 = 12` looks like it should fit in two separate calls of 6 each against a capacity of 10?
2. In `offer()`, if the request overflows, does `bucket.level` change at all? Point to the line (or absence of a line) that answers this.
3. `leak()` floors `bucket.level` at `0` rather than letting it go negative. Where would a negative `level` cause a problem in `offer()` if that floor weren't there?
4. Between a token bucket refusing a request (`Throttled`) and a leaky bucket refusing one (`Overflowed`), which of the two is rejecting because it has too little, and which is rejecting because it already has too much? Answer using only the field comparisons in each file's core function.
5. Given identical `capacity`, `rate_per_sec` / `leak_per_sec`, and timing, is it possible to construct starting conditions where a token bucket and a leaky bucket give the *same* accept/reject verdict for the same burst? What would have to be true about each bucket's starting balance/level for that to happen?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/qos/session_03_walkthrough.py
```

The walkthrough fills a leaky bucket's level with arrivals, shows an immediate overflow when there's no time to drain, shows time passing opening up room, shows a long idle period flooring the level at zero, and finishes with the headline side-by-side: an identical capacity-sized burst under identical timing passes the token bucket and overflows the leaky bucket.

## Done When

The learner can say all of the following without looking at notes:

- "A leaky bucket is a token bucket with two signs flipped: arrivals add instead of subtract, and time subtracts instead of adds."
- "A token bucket rejects because the balance is too low; a leaky bucket rejects because the backlog is already too high."
- "Under identical capacity and timing, a token bucket permits a capacity-sized burst outright; a leaky bucket smooths it and overflows on the same burst — same two variables, opposite temperament."

## References

- RFC 2475 — An Architecture for Differentiated Services (general framing for traffic conditioning and the leaky-bucket / token-bucket family of shapers)
