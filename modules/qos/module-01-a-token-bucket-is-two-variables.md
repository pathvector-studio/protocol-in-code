# Session 01 / Module 01: A Token Bucket Is Two Variables

## Position

- Track: QoS
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/qos/module-01/index.html`
- Source file: `src/protocol_in_code/qos/token_bucket.py`
- Walkthrough script: `examples/qos/session_01_walkthrough.py`

## Core Question

What actually decides whether a request is allowed or throttled, and why does that decision need no queue, no timer, and no scheduler?

## Outcome

By the end of this session, the learner should be able to:

- name the two fields that fully determine a token bucket's behavior
- explain why `try_consume()` refills before it spends
- explain why the same request can be throttled at one moment and allowed a few seconds later with no code change and no external action
- contrast a token bucket's self-refill with QUIC's externally-granted credit

## Read Order

1. Read the module docstring
2. Read `ConsumeOutcome`
3. Read `TokenBucket`
4. Read `ConsumeResult`
5. Read `try_consume()`
6. Run `examples/qos/session_01_walkthrough.py`

## Read It Like Code

```python
TokenBucket(
    capacity,
    tokens,
    rate_per_sec,
    last_refill_at,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `capacity` | The ceiling. Refill never pushes `tokens` past this, no matter how long the bucket sits idle. |
| `tokens` | The balance available right now. Every `try_consume()` call reads and rewrites this. |
| `rate_per_sec` | How fast the balance grows on its own, purely from elapsed time. |
| `last_refill_at` | When the balance was last brought up to date. Refill math is anchored here, not to a wall clock. |

## Decision Flow

```text
try_consume(bucket, n, now):
  refill bucket up to `now` first        -> tokens may grow, last_refill_at moves to now
  tokens < n                             -> Throttled (balance unchanged after refill)
  otherwise                              -> Allowed (n subtracted from tokens)
```

## Reading Lens

The important move in this session is to stop thinking of "rate limiting" as a black box and start asking:

- what is `bucket.tokens` right before this call, and what is it right after?
- did `try_consume()` get called with a `now` that is later than `last_refill_at`? If so, a refill happened first, silently, inside the same call.
- compare this file to `src/protocol_in_code/quic/flow_control.py`. QUIC's `CreditAccount` also gates an action behind a balance, but its `limit` only ever rises when a peer calls `grant()` — the balance never grows unless another party explicitly says so. A `TokenBucket`'s `tokens` grows on its own, for free, just because time passed. Same shape, opposite source of truth: QUIC's ceiling is raised by someone else; a token bucket's floor rises by the clock.

## Toy Model Boundary

Real token bucket implementations often track fractional tokens with high-resolution clocks (nanoseconds or a monotonic counter), and production rate limiters frequently layer multiple buckets (per-user, per-IP, global) with different capacities and rates. This lesson uses one bucket, one integer clock, and float token math so the refill arithmetic stays visible.

There is no packet queue here. `try_consume()` returns `Allowed` or `Throttled` — a real shaper sitting in front of a queue might delay a request instead of rejecting it outright. This toy only accepts or rejects.

## Code Landmarks

### `TokenBucket`

A plain mutable dataclass. No methods, no clock inside it — every operation on it is a free function that takes `now` as an argument.

### `try_consume()`

The whole session in one function. Read its first line closely: refill happens before the balance is even checked against `n`. This is why a request that would be throttled right now can be allowed a moment later without a separate "refill tick" ever running — the refill is folded into the very call that spends tokens.

### The module docstring's QUIC contrast

This is not decoration. The docstring names `quic/flow_control.py` directly and states the difference in one sentence: QUIC's credit only grows via a peer's `grant()`; a token bucket refills itself from elapsed time. Read `refill.py`'s import at the top of this file (`from .refill import compute_refill`) to see where that self-refill math actually lives — Session 02 covers it.

## Failure Questions

Use the source file to answer these:

1. At `now=0`, a fresh bucket with `capacity=10, tokens=10` allows a request for all 10 tokens. Why does this succeed even though no time has passed and no refill could have occurred?
2. Immediately after that request, `bucket.tokens == 0`. A second request for 1 token at the same `now` is `Throttled`. Why doesn't calling `try_consume()` again trigger a refill that would rescue this request?
3. `try_consume()` calls `compute_refill()` on every single call, even when the request is going to be throttled anyway. What does this tell you about whether `bucket.last_refill_at` moves on a throttled call?
4. If `n` is larger than `capacity` itself, can this request ever be `Allowed`, no matter how long the bucket is left idle? Point to the line that guarantees the answer.
5. Where in `try_consume()` does the returned `ConsumeResult.tokens_remaining` get its value from — before or after the spend on an `Allowed` outcome? What about on a `Throttled` outcome?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/qos/session_01_walkthrough.py
```

The walkthrough drains a bucket to zero, shows an immediate second request throttled, then shows the same size of request allowed again once enough time has passed — the self-refill headline — and finally shows that a long idle period caps the refill at capacity rather than letting it grow without bound.

## Done When

The learner can say all of the following without looking at notes:

- "A token bucket is just a balance and a timestamp — everything else is arithmetic on those two fields."
- "Refill happens inside `try_consume()`, before the spend check, not on a separate schedule."
- "A token bucket refills itself from elapsed time; QUIC's flow-control credit only grows when a peer grants it. Same balance-gates-an-action shape, opposite source of truth."

## References

- RFC 2475 — An Architecture for Differentiated Services (general framing for traffic conditioning and rate control)
- RFC 2697 — A Single Rate Three Color Marker (srTCM), which formalizes token-bucket-style metering
