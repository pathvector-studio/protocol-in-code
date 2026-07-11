# Session 05 / Module 05: The Timer Learns the Network

## Position

- Track: TCP
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/tcp/module-05/index.html`
- Source file: `src/protocol_in_code/tcp/rto.py`
- Walkthrough script: `examples/tcp/session_05_walkthrough.py`

## Core Question

How does TCP decide how long to wait before declaring a segment lost, when the "right" answer changes every round trip?

## Outcome

By the end of this session, the learner should be able to:

- explain why the very first RTT sample is treated differently from every sample after it
- state the RTO formula and name which term makes it react to jitter, not just average delay
- explain why RTO has a floor and a ceiling instead of being computed unclamped
- describe what happens to the timer on a second, third, and fourth consecutive timeout

## Read Order

1. Read `RttEstimator`
2. Read `observe()`
3. Read `rto()`
4. Read `on_timeout()`
5. Run `examples/tcp/session_05_walkthrough.py`

## Read It Like Code

```python
RttEstimator(
    srtt,
    rttvar,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `srtt` | The smoothed round-trip time. `None` means "no sample has ever arrived." |
| `rttvar` | The smoothed mean deviation of samples from `srtt`. This is what lets RTO widen when the network gets noisy, not just slow. |

## Decision Flow

```text
srtt is None                -> seed: srtt = sample, rttvar = sample / 2
srtt is not None            -> update: rttvar first (from the old srtt), then srtt
rto() with no samples yet   -> MIN_RTO_MS
rto() with samples          -> clamp(srtt + 4*rttvar, MIN_RTO_MS, MAX_RTO_MS)
on_timeout()                -> clamp(current_rto * 2, ..., MAX_RTO_MS)
```

## Reading Lens

The important move in this session is to stop thinking of "the RTT" as a single number the code looks up, and start asking:

- has `observe()` ever run on this estimator, or is `srtt` still `None`?
- when `rttvar` updates, does it use the *old* `srtt` or the *new* one? (Read the two assignment lines in order — this matters.)
- what does `rto()` return when the network is silky smooth versus when one sample just spiked?
- after a timeout, is the next RTO computed fresh from `srtt`/`rttvar`, or is it just the old RTO doubled?

## Toy Model Boundary

Real TCP stacks apply Karn's algorithm: a sample from a retransmitted segment is never trusted, because there's no way to know which copy the ACK is acknowledging. This toy's `observe()` takes a `sample_ms` at face value with no notion of "was this segment retransmitted," so it will happily corrupt `srtt` with a bad sample if you feed it one. The real protocol also has the TCP timestamps option (RFC 7323), which sidesteps the ambiguity entirely by echoing a timestamp instead of inferring RTT from ACK timing — this toy has no such option.

RTO here is a pure function of `(srtt, rttvar)` plus two constants; there's no retransmission-count state feeding back into anything except `on_timeout()`'s doubling, and that doubling is not itself stored anywhere — the caller is responsible for remembering the current RTO across calls.

## Code Landmarks

### `RttEstimator`

Two mutable fields, one of which starts as `None`. That `None` is not a bug to guard against — it's the signal `observe()` branches on to decide "is this the first sample."

### `observe()`

The reading target. Two completely different code paths hang off `estimator.srtt is None`. The seeding branch (`srtt = sample`, `rttvar = sample / 2`) only ever runs once per estimator's lifetime. Every later call takes the EWMA branch: `rttvar` is recomputed first, using the *previous* `srtt` — read the order of the two assignment lines carefully, because computing `srtt`'s update before `rttvar`'s would silently change the numbers.

### `rto()`

One formula: `srtt + 4*rttvar`. The `4*` is what makes RTO responsive to *variance*, not just the mean — a network with a stable 100ms RTT and a network with an RTT bouncing between 20ms and 180ms can have the same `srtt` but very different `rto()` results. Both the no-sample case and the computed case pass through the same `min(MAX_RTO_MS, max(MIN_RTO_MS, ...))` clamp.

### `on_timeout()`

A one-line exponential backoff: `current_rto_ms * 2`, capped. Notice this function does not touch `RttEstimator` at all — the caller owns the current RTO value and must pass it back in. The estimator itself is not "aware" of timeouts.

## Failure Questions

Use the source file to answer these:

1. If `observe()` is never called, what does `rto()` return, and which line in the source guarantees that?
2. On the *second* call to `observe()`, is `rttvar` computed using the `srtt` value from before or after that same call updates it?
3. Two estimators both end up with `srtt = 900`. One has `rttvar = 5`, the other `rttvar = 50`. Which produces the larger `rto()`, and by how much? (Watch what the clamp does to the first one.)
4. A fresh estimator receives one sample of 8ms. `srtt + 4*rttvar` computes to 24. What does `rto()` actually return, and which constant is responsible?
5. Starting from `on_timeout(1500)`, what is the result after three consecutive calls, each time feeding the previous result back in? Which single line does all three multiplications?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tcp/session_05_walkthrough.py
```

The walkthrough seeds an estimator with one sample, feeds it a run of stable samples to watch RTO tighten, injects one spiky sample to watch RTO widen, then doubles the timer via `on_timeout()` twice — once normally, once already at the ceiling.

## Done When

The learner can say all of the following without looking at notes:

- "The first sample seeds the estimator; every sample after that nudges it with the 7/8 + 1/8 and 3/4 + 1/4 weights."
- "RTO reacts to *how much samples disagree*, not just how big they are — that's what `rttvar` and the `4*` are for."
- "A timeout doubles whatever RTO currently is; it doesn't recompute from `srtt` and `rttvar`."

## References

- RFC 6298 Section 2 (computing the retransmission timer)
- RFC 6298 Section 5 (managing the RTO timer, including the exponential backoff on retransmission)
