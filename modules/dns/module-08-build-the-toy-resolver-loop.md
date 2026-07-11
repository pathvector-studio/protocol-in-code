# Session 08 / Module 08: Build the Toy Resolver Loop

## Position

- Track: DNS
- Session: 08
- Site lesson: `pathvector-site/courses/protocols-in-code/dns/module-08/index.html`
- Source file: `src/protocol_in_code/dns/resolver.py`
- Walkthrough script: `examples/dns/session_08_walkthrough.py`

## Core Question

What does the smallest readable resolver look like when validation, cache, tree walk, and CNAME restart are connected in one loop?

## Outcome

By the end of this session, the learner should be able to:

- name the four stages one query passes through, in order
- explain why the cache check sits between validation and the walk
- trace a CNAME that crosses from one zone into another
- read a resolution trace and say which stage produced each line

## Read Order

1. Read `ResolveSource` and `ResolveResult`
2. Read `ToyResolver.resolve()` top to bottom
3. Map each block back to its session: validate (01), cache (04), walk (02), CNAME restart (06)
4. Run `examples/dns/session_08_walkthrough.py`
5. Read the printed traces and label each line with its stage

## Read It Like Code

```python
ToyResolver(
    zones,
    cache,
    clock,
    default_ttl,
)
```

## Pipeline

```text
validate_question()   invalid -> Rejected, stop
lookup(cache, now)    hit     -> Cache, stop
walk_from_root()      found   -> store(), Network, stop
CNAME at this name?   yes     -> restart walk with target (bounded)
                      no      -> Failed
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `zones` | The world this resolver can see. Session 02's structure, unchanged. |
| `cache` | Session 04's structure. It is state: the same query gives different sources over time. |
| `clock` | Time is a field advanced by `tick()`, so every scenario replays identically. |
| `default_ttl` | The lifetime stamped onto every network answer as it enters the cache. |

## Reading Lens

The important move in this session is to stop reading the resolver as one black box and start asking:

- which stage answered this query?
- which earlier session's function is running at this line of the trace?
- what state changed as a side effect, and where will that show up next query?

## Toy Model Boundary

This resolver connects four of the track's components. It deliberately leaves out the response classification from Session 03 and the server fallback from Session 07, because the zone dict never times out and never lies. The exercise at the end of this module is to decide where those two would plug in.

The answer is cached under the original question, so an aliased answer is served from cache without replaying the CNAME chain. Real resolvers cache each link separately.

## Code Landmarks

### `ResolveSource`

Four values: Rejected, Cache, Network, Failed. Every resolution ends as exactly one of these, and the walkthrough asserts on them.

### The `for` loop in `resolve()`

The CNAME restart from Session 06, rebuilt over real zone walks instead of a flat dict. The loop bound does double duty as chain budget.

### `trace`

Every stage appends what it decided. This is the habit the whole track teaches: a resolver that can say which branch it took is a resolver you can debug.

### `tick()`

The walkthrough's final scenario works only because time is explicit: advance the clock past the TTL and the same question flips from Cache back to Network.

## Failure Questions

Use the source file to answer these:

1. Which stages run for a query that ends as Rejected? Which are skipped?
2. Why does the second identical query return `Cache` while the first returned `Network`?
3. In the `app.example.com` scenario, how many full tree walks happen, and why?
4. What two conditions can produce `Failed`, and how does the trace tell them apart?
5. Where would Session 07's `try_servers()` fit into this pipeline?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dns/session_08_walkthrough.py
```

The walkthrough runs six queries against one resolver instance and prints the full decision trace for each, including cache expiry driven by the clock.

## Done When

The learner can say all of the following without looking at notes:

- "A resolver is validate, then cache, then walk, then restart — in that order, with early exits."
- "The cache makes the resolver stateful: the same question has different sources at different times."
- "Every line of the trace corresponds to one earlier session of this track."

## References

- RFC 1034 Section 5.3.3 (the resolver algorithm this loop compresses)
- RFC 1035 Section 7
- RFC 8499 (full-service resolver terminology)
