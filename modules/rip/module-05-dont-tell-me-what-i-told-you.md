# Session 05 / Module 05: Don't Tell Me What I Told You

## Position

- Track: RIP
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/rip/module-05/index.html`
- Source file: `src/protocol_in_code/rip/split_horizon.py`
- Walkthrough script: `examples/rip/session_05_walkthrough.py`

## Core Question

If the cure for count-to-infinity isn't smarter math, what is it, and where exactly does it run?

## Outcome

By the end of this session, the learner should be able to:

- state the split horizon rule in one sentence: never advertise a route back toward the neighbor it came from
- name the one field `advertisable()` inspects to make that decision
- explain the difference between omitting a route and poisoning it
- predict, for any given neighbor, which routes a table will and will not advertise to it

## Read Order

1. Read the module docstring
2. Read `advertisable()`
3. Read `advertisable_with_poison()`
4. Run `examples/rip/session_05_walkthrough.py`

## Read It Like Code

```python
advertisable(
    table,
    to_neighbor,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `route.next_hop` | The single value both functions test. If it equals `to_neighbor`, this route came from (or through) the router we're about to speak to. |
| `route.metric` | Left untouched by plain split horizon; replaced with `INFINITY` by poisoned reverse. |
| `to_neighbor` | Not a table lookup — the caller supplies who they're about to speak to, once per outbound advertisement. |

## Decision Flow

```text
for each route in table, sorted by prefix:
  route.next_hop == to_neighbor
    plain split horizon    -> omit the route entirely
    poisoned reverse        -> include it, but with metric = INFINITY
  route.next_hop != to_neighbor
    both functions          -> include it at its real metric
```

## Reading Lens

The important move in this session is to stop thinking about the rumor's content and start asking, for every route in the table:

- who is `next_hop` for this route, and is that the same router I'm about to advertise to?
- if I omit this route, does the neighbor even notice, or does it just wait out a timeout?
- if I poison it instead, what changes about how fast the neighbor can react?

## Toy Model Boundary

Real RIP routers apply split horizon per interface — a route learned via one interface is filtered only on advertisements sent back out that same interface, and the same route may be freely advertised out every other interface. This module has no interface concept at all; `to_neighbor` stands in for "the interface facing that neighbor," and the single-hop, single-link topology in this track's simulations makes neighbor and interface interchangeable. That collapse is intentional — it keeps the filter's logic visible without needing an interface table.

## Code Landmarks

### The module docstring

Names the previous session's function directly: "count_to_infinity.py shows the disease... The cure lives here." Read it as the thesis statement for this whole module: the fix is a send-side filter, not smarter math on the receiving end.

### `advertisable()`

One `if route.next_hop == to_neighbor: continue`. The entire split horizon rule is a single skipped iteration in a loop that otherwise just copies `(prefix, metric)` pairs.

### `advertisable_with_poison()`

Same loop, same condition, but the `continue` becomes an `else` that appends `(prefix, INFINITY)` instead of `(prefix, route.metric)`. Read the two functions side by side — every line matches except the one branch.

## Failure Questions

Use the source file to answer these:

1. `advertisable()` compares `route.next_hop == to_neighbor`. Why is `next_hop` the correct field to check here instead of `learned_from` (even though in this track's simulations the two are always equal)?
2. A table has three routes, two learned from neighbor X and one learned locally. What does `advertisable(table, to_neighbor="X")` return, and how many routes does it omit?
3. Both functions iterate `sorted(table.routes.items())`. What would change about the walkthrough's assertions if the iteration order were not sorted?
4. The docstring says poisoned reverse "converges faster because the neighbor doesn't have to wait for a timeout to notice the route is gone." Given that this toy has no timeout mechanism at all, what does that sentence tell you about a real RIP deployment that this module doesn't simulate?
5. `advertisable_with_poison()` never calls `advertisable()`, and `advertisable()` never calls `advertisable_with_poison()`. Given how similar their loop bodies are, what would be lost — for a reader learning the two behaviors as *alternatives* — if one were implemented by calling the other and patching the result?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/rip/session_05_walkthrough.py
```

The walkthrough builds one table with two routes learned from two different neighbors, then shows the same route disappearing from the advertisement to its source neighbor while staying present toward every other neighbor — and reappearing at `INFINITY` once poisoned reverse is used instead of plain omission.

## Done When

The learner can say all of the following without looking at notes:

- "Split horizon is a send-side filter: one field checked, one route skipped, nothing about the receiving end changes."
- "Poisoned reverse doesn't hide the loop-prone route — it announces it as dead, on purpose, instead of staying silent."
- "`advertisable()` and `advertisable_with_poison()` agree on every route except the one whose `next_hop` is the neighbor being spoken to."

## References

- RFC 2453 Section 2.3 (Split Horizon)
- RFC 2453 Section 2.3 (Split Horizon with Poisoned Reverse)
