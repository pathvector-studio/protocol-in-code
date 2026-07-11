# Session 03 / Module 03: Sixteen Means Unreachable

## Position

- Track: RIP
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/rip/module-03/index.html`
- Source file: `src/protocol_in_code/rip/infinity.py`
- Walkthrough script: `examples/rip/session_03_walkthrough.py`

## Core Question

RIP needs a metric value that fits in the same integer field as every real distance but means "not reachable at all." Why is that value 16 — not 255, not a billion — and what does picking a small number actually buy?

## Outcome

By the end of this session, the learner should be able to:

- state `INFINITY = 16` and explain why the value is deliberately small rather than deliberately large
- give the exact boundary condition `is_unreachable()` uses, and evaluate it at 15 and at 16
- explain what `clamp_metric()` does to a sum that overshoots 16, with a concrete example
- state what `poison()` changes about a route and what it leaves untouched

## Read Order

1. Read the module docstring
2. Read `INFINITY`
3. Read `is_unreachable()`
4. Read `clamp_metric()`
5. Read `poison()`
6. Run `examples/rip/session_03_walkthrough.py`

## Read It Like Code

```python
is_unreachable(metric)   # metric >= INFINITY
clamp_metric(metric)     # min(metric, INFINITY)
poison(route)            # replace(route, metric=INFINITY)
```

## Fields That Matter

There is no dataclass introduced in this module — `infinity.py` is three small functions and one constant, operating on plain integers and on the `RipRoute` defined in session 01.

| Name | Why it matters |
|---|---|
| `INFINITY` | `16`. The one constant every function in this module measures against. |
| `metric` (in `is_unreachable`, `clamp_metric`) | A raw integer distance, already summed by the caller — session 02's `candidate_metric` computation is the main caller. |
| `route` (in `poison`) | A full `RipRoute` from session 01. `poison()` returns a new one rather than mutating — `RipRoute` is frozen, so there is no other option. |

## Decision Flow

```text
is_unreachable(metric):
  metric >= INFINITY   -> True
  otherwise             -> False

clamp_metric(metric):
  metric > INFINITY    -> INFINITY
  otherwise             -> metric   (min() collapses both cases into one expression)

poison(route):
  -> RipRoute(route.prefix, INFINITY, route.next_hop, route.learned_from)
     (every field but metric is copied unchanged)
```

## Reading Lens

This module is pure and tiny in exactly the way `tcp/seqnum.py` is pure and tiny: no dataclasses to inspect, no branching state machine, just arithmetic that has to be exactly right at one boundary. The important move is to stop treating "16" as an arbitrary magic number and start asking:

- what specific comparison operator does `is_unreachable()` use at the boundary — is `16` itself unreachable, or is `17` the first unreachable value?
- when `clamp_metric()` fires, what real-world event does an overshoot like `15 + 1 = 16` or `advertised 100` represent?
- `poison()` builds a new `RipRoute` with one field changed. Which fields does it have to carry forward unchanged for the result to still mean "this is a route to the same destination, just now marked dead"?

## Toy Model Boundary

The module docstring itself sets up the next session: a small infinity bounds how many rounds a routing loop can circulate before the bad rumor tops out, at the cost of also bounding how large a real network RIP can cover (15 hops maximum, since 16 means unreachable). This module only implements the boundary check and the poisoning operation — it does not implement the loop, the timers, or the periodic-update behavior that actually drives a metric upward round by round. That is `count_to_infinity.py`'s job, in the session this one is deliberately positioned before.

This module's specific numbers — `INFINITY = 16`, and the discussion of hop-count semantics — are RIPv2's. RIPng (RFC 2080) reuses the same metric field and the same value of 16 for IPv6, but carries it differently on the wire; this module does not model that difference.

## Code Landmarks

### Module docstring

Frames `16` not as a limit on network size so much as a deliberately short fuse on how long a bad rumor can circulate — a design tradeoff, not an accident. Read this before the functions below; it is the argument the Failure Questions test.

### `is_unreachable()`

One comparison, `metric >= INFINITY`. Note the `>=`, not `>` — a metric of exactly `16` already counts as unreachable, it does not have to exceed `16` first.

### `clamp_metric()`

`min(metric, INFINITY)` — a single expression that leaves any metric of `16` or below untouched and caps anything above it at exactly `16`. This is the function session 02's `process_advertisement()` calls on every candidate before it ever compares metrics, so no route in the table can ever silently carry a metric above `16`.

### `poison()`

`dataclasses.replace(route, metric=INFINITY)` — the only field touched is `metric`; `prefix`, `next_hop`, and `learned_from` all pass through unchanged. Poisoning a route does not erase who it came from, it just declares the distance to it infinite.

## Failure Questions

Use the source file to answer these:

1. `is_unreachable(16)` and `is_unreachable(15)` — what does each return, and which operator (`>=` versus `>`) makes 16 itself count as unreachable rather than the last reachable hop count?
2. `clamp_metric(15 + 1)` and `clamp_metric(100)` both return the same value. What does that tell you about how much information `clamp_metric()` preserves about *how far* a metric overshot infinity?
3. `poison()` uses `dataclasses.replace()` rather than constructing a new `RipRoute` field by field. What has to be true about `RipRoute` (see session 01) for `replace()` to be usable at all here?
4. After `poison(route)`, is `poisoned.learned_from == route.learned_from`? Read the `replace()` call to justify your answer — does poisoning a route change who it was learned from?
5. The module docstring says a small infinity is "a deliberately short fuse," not a network-size limit as an end in itself. If `INFINITY` were `256` instead of `16`, what specifically about `is_unreachable()` and `clamp_metric()` would still work correctly, and what would only change in degree (how long a bad rumor could circulate) rather than in kind?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/rip/session_03_walkthrough.py
```

The walkthrough clamps `15 + 1` and a wildly overshot `100` to confirm both land on exactly `16`, checks the `is_unreachable()` boundary at `16` and at `15`, and poisons a route to confirm the metric becomes `16` while `prefix`, `next_hop`, and `learned_from` all survive unchanged.

## Done When

The learner can say all of the following without looking at notes:

- "16 is `INFINITY` — small on purpose, so a routing loop's metric tops out in a handful of rounds instead of climbing forever."
- "`is_unreachable()` uses `>=`, so a metric of exactly 16 is already unreachable, not the last valid hop count."
- "`poison()` only ever changes `metric`; every other field of the route — including who it was learned from — is carried forward untouched."

## References

- RFC 2453 Section 3.8 (Distance Metric: RIP's use of hop count and the choice of 16 as infinity)
- RFC 2453 Section 3.10 (Timers, referenced here only to note what this toy model deliberately omits — the periodic and triggered-update timing that actually drives count-to-infinity)
