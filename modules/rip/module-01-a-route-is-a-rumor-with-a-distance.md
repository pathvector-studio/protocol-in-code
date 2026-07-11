# Session 01 / Module 01: A Route Is a Rumor with a Distance

## Position

- Track: RIP
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/rip/module-01/index.html`
- Source file: `src/protocol_in_code/rip/route.py`
- Walkthrough script: `examples/rip/session_01_walkthrough.py`

## Core Question

An OSPF Router-LSA is a fact a router asserts about its own links, flooded unchanged across the area. A `RipRoute` is neither of those — it is one neighbor's claim about hop count, already folded together with everything that neighbor believed before it. What does it mean to trust a number like that, and what does the code let you check before you do?

## Outcome

By the end of this session, the learner should be able to:

- name the four fields of `RipRoute` and explain what each one commits to
- explain why RIP has no LSA-equivalent — no shared, independently verifiable fact to recompute a route from
- state the two ways a metric can be invalid, and the one range that is valid
- explain `better()` in one sentence, and say what it does on a tie

## Read Order

1. Read the module docstring
2. Read `RipRoute`
3. Read `RouteValidity`
4. Read `validate_route()`
5. Read `better()`
6. Run `examples/rip/session_01_walkthrough.py`

## Read It Like Code

```python
RipRoute(
    prefix,
    metric,
    next_hop,
    learned_from,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `prefix` | The destination this claim is about. |
| `metric` | Hop count as the neighbor reported it, already including the hop it took to reach us. This is the number the whole track is built around. |
| `next_hop` | Where to actually forward packets for `prefix` — usually the neighbor itself. |
| `learned_from` | Which neighbor is the source of this belief. Session 02 reads this field to decide whether to trust bad news. |

## Decision Flow

```text
metric < 0    -> NEGATIVE_METRIC (invalid)
metric > 16   -> METRIC_TOO_HIGH (invalid)
otherwise     -> VALID            (0 through 16, inclusive)

better(a, b):
  a.metric < b.metric  -> True   (a wins)
  otherwise             -> False (b keeps it, ties included)
```

## Reading Lens

The important move in this session is to stop asking "is this route correct?" and start asking "whose claim is this, and how far has it traveled?"

- what does `learned_from` tell you that `next_hop` does not?
- `validate_route()` only checks that a number is a plausible hop count — it says nothing about whether the hop count is *true*. What would it take to know that?
- `better()` compares two integers. What information about *how* each metric was produced is invisible to it by the time it runs?

## Toy Model Boundary

Real RIP also carries route tags and, in RIPv2, subnet masks and authentication data on the wire — none of that is modeled here. `RipRoute` keeps exactly the four fields the rest of this track's logic touches. There is also no timer field: nothing here says how old this claim is or when it should be discarded. That question belongs to session 04's aging and count-to-infinity material, not to this one.

## Code Landmarks

### Module docstring

Read this before the code. It states the thesis the whole session is built on: an OSPF LSA is a fact, independently checkable by every router that floods it; a `RipRoute` is hearsay, and there is no shared map to recompute it from. Everything downstream — why session 02 has to trust `learned_from`, why session 03's infinity has to be small — follows from there being no ground truth to fall back on.

### `RipRoute`

Frozen by design. A route that changes in place would blur the line between "a new claim arrived" and "the old claim mutated" — session 02's `process_advertisement()` always builds a fresh `RipRoute` rather than editing one.

### `validate_route()`

Two failure cases, not one. `NEGATIVE_METRIC` catches a hop count that cannot exist; `METRIC_TOO_HIGH` catches a hop count that exceeds the ceiling session 03 explains. Note that `16` itself is valid — infinity is a real, meaningful value in this scheme, not an error.

### `better()`

The main reading target. One comparison, `a.metric < b.metric`, and the docstring calls out that this is the third time this course does selection-by-comparison: OSPF's `select_best_route()` in `ospf/cost.py` picks a winner by `total_cost` (after a route-type check), and BGP's `select_best_path()` in `bgp/best_path.py` picks a winner by walking a multi-step attribute chain (weight, then local preference, then AS-path length, then origin, then next-hop as a final tiebreak). RIP does the same job — pick one winner among candidates — with a single integer and a strict `<`. Same shape every time; the rulebook just gets thinner as you move from BGP to OSPF to RIP.

## Failure Questions

Use the source file to answer these:

1. `RipRoute` has no field that records *when* a metric was learned. Which later session's material does that omission set up, and why does `route.py` deliberately leave it out?
2. `validate_route()` accepts `metric == 16` as `VALID`. Given `RouteValidity.METRIC_TOO_HIGH` triggers only above 16, what does that tell you about whether "unreachable" and "invalid" are the same concept in this code?
3. `better(a, b)` uses strict `<`, not `<=`. Trace what happens when `a.metric == b.metric` — does either route ever get reported as better than the other?
4. The docstring names two other files that also do selection-by-comparison. Which single field does OSPF's `select_best_route()` compare after route type, and how does that compare in complexity to what BGP's `select_best_path()` compares?
5. `RipRoute` is `frozen=True`. Find where `route.py` or a file that imports it would need to replace a route rather than mutate one — what does freezing the dataclass force the caller to do instead of assignment?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/rip/session_01_walkthrough.py
```

The walkthrough builds one valid route and prints it, then shows both ways `validate_route()` rejects a metric (negative, and over 16), confirms `16` itself is valid, and finally runs `better()` on a closer route, a farther route, and a tie — showing that a tie favors neither side.

## Done When

The learner can say all of the following without looking at notes:

- "A `RipRoute` is one neighbor's claim, not a verified fact — there is no LSA-equivalent to check it against."
- "A metric is valid from 0 through 16; only negative or over-16 values are rejected, and 16 itself means something, not nothing."
- "`better()` is strict `<`, so a tie changes nothing — the incumbent route is not replaced."

## References

- RFC 2453 Section 3.1 (protocol overview: distance vectors as hop counts, no independent verification)
- RFC 2453 Section 4 (RIPv2 message format: the fields a real route advertisement carries beyond what this toy models)
