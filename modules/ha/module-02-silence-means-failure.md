# Session 02 / Module 02: Silence Means Failure

## Position

- Track: HA (VRRP+BFD)
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/ha/module-02/index.html`
- Source file: `src/protocol_in_code/ha/vrrp_timeout.py`
- Walkthrough script: `examples/ha/session_02_walkthrough.py`

## Core Question

A VRRP backup never asks "are you alive?" — so how does it decide, correctly, that the master is gone?

## Outcome

By the end of this session, the learner should be able to:

- explain why failover is inferred from absence rather than detected as an event
- compute `Skew_Time` for a given priority and say why it shrinks as priority rises
- state the exact comparison `master_is_down()` makes, including which side of the boundary counts as "down"
- explain what a single call to `heartbeat()` does to that boundary

## Read Order

1. Read the module docstring at the top of the file
2. Read `ADVERTISEMENT_INTERVAL`
3. Read `master_down_interval()`
4. Read `BackupWatch`
5. Read `heartbeat()`
6. Read `master_is_down()`
7. Run `examples/ha/session_02_walkthrough.py`

## Read It Like Code

```python
BackupWatch(
    last_heard_at,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `last_heard_at` | The only state a backup keeps about the master. Everything else is arithmetic on this one timestamp. |

## Decision Flow

```text
master_down_interval(priority):
  skew = ((256 - priority) * ADVERTISEMENT_INTERVAL) // 256
  return 3 * ADVERTISEMENT_INTERVAL + skew

master_is_down(watch, priority, now):
  now >= watch.last_heard_at + master_down_interval(priority)  -> True  (down)
  otherwise                                                     -> False (still up)
```

## Reading Lens

The important move in this session is to stop asking "did a failure event fire?" and start asking:

- what time did the master last speak, per `last_heard_at`?
- how long is this particular backup willing to wait, given its own priority?
- has `now` crossed `last_heard_at + master_down_interval(priority)` yet — and is the crossing point itself included?

Nothing in this file reacts to a failure. `master_is_down()` is a pure comparison, callable at any time, with no side effect — the "detection" is just asking the question at the right moment.

## Toy Model Boundary

Real VRRP backups also track a Skew_Time-adjusted wait specifically for the very first advertisement after startup, and the interval can itself be learned from the master's advertised `Advertisement_Interval` rather than assumed fixed. This module hard-codes `ADVERTISEMENT_INTERVAL = 1000` and only models steady-state timeout math — no startup grace period, no learned interval.

## Code Landmarks

### `master_down_interval()`'s docstring

The skew is the reading target: `Skew_Time = ((256 - priority) * Advertisement_Interval) / 256`. A **higher** priority produces a **smaller** `256 - priority`, hence a smaller skew, hence a shorter total wait. The best-priority backup always finishes counting first — the skew turns what would otherwise be a tie among multiple backups into an ordered race with a predictable winner.

### The integer division in `master_down_interval()`

`// 256`, not `/ 256`. Skew_Time is defined in milliseconds and RFC 5798 specifies it as an integer computation; using `//` instead of true division keeps `master_down_interval()`'s return value an `int` that can be compared directly against another `int`, `now`, with no floating-point rounding to reason about.

### `master_is_down()`'s comparison

`now >= watch.last_heard_at + master_down_interval(priority)`. The operator is `>=`, not `>` — the exact millisecond the interval elapses already counts as down. This is the same boundary convention as `dns/cache.py`'s `entry_is_expired()`: the threshold instant belongs to the "past" outcome, not the "still valid" one.

### `heartbeat()`

One line: `watch.last_heard_at = now`. It doesn't touch priority, doesn't touch the interval — it only moves the anchor that `master_is_down()` measures from. Every subsequent down-check is relative to this new anchor.

## Failure Questions

Use the source file to answer these:

1. For `priority=254`, what is `Skew_Time` before it's added to `3 * ADVERTISEMENT_INTERVAL`? Compute `(256 - 254) * 1000 // 256` by hand and confirm it matches what the walkthrough prints.
2. Why does `master_down_interval()` use `//` (integer division) instead of `/`? What type would `Skew_Time` be if `/` were used, and what would that break in `master_is_down()`'s comparison?
3. At `now == watch.last_heard_at + master_down_interval(priority)` exactly, does `master_is_down()` return `True` or `False`? Which comparison operator decides this?
4. Two backups, priority 254 and priority 100, both stop hearing the master at the same `last_heard_at`. Which one's `master_is_down()` returns `True` first, and by how many milliseconds (using `ADVERTISEMENT_INTERVAL = 1000`)?
5. `heartbeat()` takes `watch` and `now` but not `priority`. Why doesn't it need `priority` at all — what does that tell you about which value actually depends on priority?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/ha/session_02_walkthrough.py
```

The walkthrough prints `master_down_interval(254)` and `master_down_interval(100)` side by side, checks the `>=` boundary one millisecond before and exactly at the threshold, and shows a `heartbeat()` call pushing that boundary forward.

## Done When

The learner can say all of the following without looking at notes:

- "A backup doesn't detect the master's failure — it infers it by comparing now against last_heard_at plus a computed interval."
- "Higher priority means a smaller skew means a shorter wait — the best backup always notices first."
- "The boundary is >=, so the exact millisecond the interval elapses already counts as down."

## References

- RFC 5798 Section 6.2 (Master_Down_Interval, Skew_Time)
- RFC 5798 Section 5.2.4 (Advertisement_Interval)
