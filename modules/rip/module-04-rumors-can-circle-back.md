# Session 04 / Module 04: Rumors Can Circle Back

## Position

- Track: RIP
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/rip/module-04/index.html`
- Source file: `src/protocol_in_code/rip/count_to_infinity.py`
- Walkthrough script: `examples/rip/session_04_walkthrough.py`

## Core Question

Why does a distance-vector router that just lost a route end up believing its own rumor came back from a neighbor, and how many rounds does that belief take to burn itself out?

## Outcome

By the end of this session, the learner should be able to:

- narrate the count-to-infinity failure as a two-router exchange, round by round
- explain why the metric climbs by exactly 2 per round, not 1
- state what event starts the climb and what value stops it
- explain why the fixed version imports `advertisable()` instead of reimplementing filtering inline

## Read Order

1. Read the module docstring in `count_to_infinity.py` — the whole failure is described in prose before any code
2. Read `RoundSnapshot` and `CountResult`
3. Read `simulate_count_to_infinity()`
4. Read `simulate_with_split_horizon()`
5. Run `examples/rip/session_04_walkthrough.py`

## Read It Like Code

```python
CountResult(
    rounds,
    converged_at,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `rounds` | One `RoundSnapshot` per exchange round — the whole climb is visible as a sequence, not a final number. |
| `converged_at` | The round number where both metrics first cross `INFINITY`. `None` if the loop runs out of `max_rounds` first. |
| `RoundSnapshot.a_metric` / `b_metric` | The two routers' current belief about the cost of the same prefix — the two numbers that should never both be climbing. |

## Decision Flow

```text
each round:
  B advertises its table to A (unfiltered)  -> A adopts/updates via Bellman-Ford
  A advertises its table to B (unfiltered)  -> B adopts/updates via Bellman-Ford
  record (a_metric, b_metric) for this round
  both metrics >= INFINITY and not yet converged  -> converged_at = this round, stop
  otherwise                                        -> next round
```

## Reading Lens

The important move in this session is to stop looking at the final metric and start asking, round by round:

- which router is currently the "source of truth" for this prefix, according to `learned_from`?
- did the router that just adopted a worse metric have any way to know that metric originated with itself?
- what is the exact round in which the rule in `update.py` — "believe your neighbor, add one" — turns from correct into circular?

## Toy Model Boundary

Real RIP implementations use triggered updates (send immediately on a change, not just on the next periodic timer) and hold-down timers (refuse to accept a worse route for a prefix for a cooldown period after a big change). Neither exists here. This module is two routers and a synchronous round-robin exchange, which is enough to see the arithmetic of the failure without needing timers, timeouts, or a third router to make the topology realistic.

## Code Landmarks

### The module docstring

Written as a narrative, not a spec: A has the prefix, loses it, and B — which only ever learned about the prefix through A — keeps offering it back. Read this before the code; the two functions below are just that story executed twice, once broken and once fixed.

### `simulate_count_to_infinity()`

Notice what is absent: no filtering. Each side calls `process_advertisement()` on the neighbor's *entire* table. That is the whole bug — not a math error, an unfiltered advertisement.

### `simulate_with_split_horizon()`

The only difference from the function above is that `table_b.routes.items()` is no longer sent directly — it goes through `advertisable(table_b, to_neighbor="A")` first. Same loop shape, same `process_advertisement()` call, one new line per direction.

### The import line

`from .split_horizon import advertisable`. This file does not define its own filtering logic. That is a design decision explained in the docstring, not an oversight — see Failure Question 4.

## Failure Questions

Use the source file to answer these:

1. In `simulate_count_to_infinity()`, why does the metric climb by 2 each round instead of 1, even though `process_advertisement()` only ever adds 1 to an advertised metric?
2. What is the very first event in the simulation that makes A's table stop matching reality, and where in the code does that event happen (hint: it happens before the loop starts)?
3. Why does the loop check `a_metric >= INFINITY and b_metric >= INFINITY` — both sides — before declaring `converged_at`, rather than stopping the moment either one crosses 16?
4. The module docstring says split horizon is "the general-purpose filter... and this module is one demonstration consuming it, not the other way around." What would be lost if `simulate_with_split_horizon()` instead inlined the `next_hop == to_neighbor` check directly, without importing from `split_horizon.py`?
5. `simulate_with_split_horizon()`'s stopping condition only checks `a_metric >= INFINITY`, not `b_metric`. Looking at the round-1 values the walkthrough asserts (A=16, B=2), why is checking only `a_metric` still correct here?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/rip/session_04_walkthrough.py
```

The walkthrough runs both simulations from the same starting tables: `simulate_count_to_infinity()` climbing by 2 a round for eight rounds before both sides finally agree the prefix is gone, and `simulate_with_split_horizon()` reaching the same correct outcome in a single round because the outbound filter stops the rumor from ever leaving the router that would have echoed it back.

## Done When

The learner can say all of the following without looking at notes:

- "A never had a real routing failure that took eight rounds to detect — it had an advertisement problem that a one-line filter fixes in one round."
- "The metric climbs by 2 a round because both routers are climbing at once, each adding 1 to what the other just told it."
- "`converged_at` is not a timeout — it's the round both sides cross INFINITY, which only happens because nothing stopped them from advertising back to their own source."

## References

- RFC 2453 Section 2.2 (Distance Vector Algorithms — the count-to-infinity problem)
- RFC 2453 Section 3.9.2 (Response Processing / route update rules)
