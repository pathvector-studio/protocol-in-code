# Session 02 / Module 02: Bellman-Ford Is a For Loop

## Position

- Track: RIP
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/rip/module-02/index.html`
- Source file: `src/protocol_in_code/rip/update.py`
- Walkthrough script: `examples/rip/session_02_walkthrough.py`

## Core Question

OSPF's SPF run in `ospf/spf.py` is Dijkstra over the whole LSDB — a graph object, a priority queue, one full recompute. RIP never sees the graph at all: it only sees what one neighbor just said. What does it mean to run Bellman-Ford when all you have is a single pass over a list of `(prefix, metric)` pairs, and what has to be true before a new number is allowed to overwrite an old one?

## Outcome

By the end of this session, the learner should be able to:

- explain why `process_advertisement()` needs no graph, no queue, and no global view of the network
- state where the "+1" is added and why it happens before any comparison
- recite the four `UpdateOutcome`s in the order the code checks for them
- explain the same-source rule from RFC 2453 §3.9.2: why a worse metric from your current source is still adopted

## Read Order

1. Read the module docstring
2. Read `UpdateOutcome`
3. Read `RoutingTable`
4. Read `process_advertisement()`
5. Run `examples/rip/session_02_walkthrough.py`

## Read It Like Code

```python
process_advertisement(
    table,       # RoutingTable, mutated in place
    neighbor,    # who sent this advertisement
    advertised,  # ((prefix, metric), ...) as the neighbor stated it
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `table.routes` | A `dict[str, RipRoute]` keyed by prefix — one best route per destination, nothing more. |
| `neighbor` | Who is speaking. Compared against `current.learned_from` to decide whether this is fresh news or an update from the same source. |
| `advertised` | Raw `(prefix, metric)` pairs — the metric as the neighbor sees it, not yet adjusted for the hop to reach us. |
| `candidate_metric` | `advertised_metric + 1`, clamped at `INFINITY`. The one hop it took to hear this claim, made visible. |

## Decision Flow

```text
for (prefix, advertised_metric) in advertised:
    candidate_metric = clamp_metric(advertised_metric + 1)
    candidate = RipRoute(prefix, candidate_metric, next_hop=neighbor, learned_from=neighbor)

    current = table.routes.get(prefix)

    current is None                        -> ADOPTED_NEW       (store candidate)
    better(candidate, current)             -> ADOPTED_BETTER    (store candidate)
    current.learned_from == neighbor       -> UPDATED_SAME_SOURCE (store candidate, even if worse)
    otherwise                              -> IGNORED_WORSE     (table unchanged)
```

## Reading Lens

The important move in this session is to stop thinking "the router recomputes routes" and start asking, one prefix at a time:

- what did the neighbor actually say, versus what does it cost me to believe them (`+ 1`)?
- is there already a route for this prefix at all?
- if the new number loses on `better()`, is that because a genuinely better path exists elsewhere, or because my own source's path got worse?

That last question is the whole session. `process_advertisement()` is not "keep the lowest metric ever seen" — it is "keep the lowest metric, unless the source I already trust is now telling me something else."

## Toy Model Boundary

Real RIP does not process every advertisement as a full replacement pass triggered synchronously by the test — it runs on periodic and triggered updates, with route timers governing when a route is aged out even without new news arriving. None of that timing machinery exists here: an advertisement arrives exactly when `process_advertisement()` is called, and that is the only clock this session has. Route tags, subnet masks, and authentication (RIPv2 wire fields) are also absent — the same simplification session 01 already named for `RipRoute` itself.

## Code Landmarks

### Module docstring

States the framing directly: no graph, no priority queue, just a single pass relaxing each edge from one neighbor's advertisement. RFC 2453 §3.9.2 is cited because it is the literal source for both rules the loop implements — add one, then decide whether to replace.

### `UpdateOutcome`

Four outcomes, and the order they are listed in the enum matches the order `process_advertisement()` checks for them: new, better, same-source, worse. That ordering is not cosmetic — it is the control flow.

### `process_advertisement()`

The main reading target. `candidate_metric = clamp_metric(advertised_metric + 1)` runs before any comparison, so every candidate the rest of the function looks at has already paid the one-hop cost — comparisons are apples to apples. The `if better(candidate, current)` check runs strictly before the `if current.learned_from == neighbor` check. That ordering matters: a candidate that is both better *and* same-source is reported as `ADOPTED_BETTER`, not `UPDATED_SAME_SOURCE` — the same-source rule only fires once the better-metric path has already failed.

## Failure Questions

Use the source file to answer these:

1. `process_advertisement()` checks `better(candidate, current)` before `current.learned_from == neighbor`. If a candidate is both better and from the current source, which `UpdateOutcome` is reported? Trace the `continue` statements to be sure.
2. RFC 2453 §3.9.2's same-source rule fires only after the better-metric check fails. What has to be true about `candidate.metric` relative to `current.metric` for `UPDATED_SAME_SOURCE` to ever be reached?
3. An advertisement from a neighbor that is *not* `current.learned_from`, with a metric that loses to `better()`, produces which outcome? Does the table change at all?
4. `candidate_metric` is computed once, before `table.routes.get(prefix)` is even checked. What would break about the `ADOPTED_NEW` case if the `+ 1` were applied only inside the `better()` branch instead?
5. `clamp_metric` is imported from `infinity.py` and applied to every candidate, not just ones that end up adopted. Why does the code clamp before comparing, rather than comparing raw sums and clamping only the value it decides to store?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/rip/session_02_walkthrough.py
```

The walkthrough runs one prefix through all four outcomes in sequence: a first advertisement from N1 (`ADOPTED_NEW`, with the `+1` visible as advertised `3` becoming stored `4`), a better one from N2 (`ADOPTED_BETTER`), a worse one from N1 — no longer the current source — that changes nothing (`IGNORED_WORSE`), a worse one from N2 — still the current source — adopted anyway (`UPDATED_SAME_SOURCE`, headlined "believe your own source"), and finally a fresh prefix advertised so high that its stored metric clamps at `16`.

## Done When

The learner can say all of the following without looking at notes:

- "Every candidate metric is `advertised + 1`, clamped at infinity, computed before any comparison happens."
- "`better()` is checked first; the same-source rule only matters once `better()` has already said no."
- "A worse metric from your current source is still adopted — RFC 2453 §3.9.2 says you believe your own source even when the news is bad."

## References

- RFC 2453 Section 3.9.2 (updating the routing table: the add-one-then-compare rule and the same-source override this module implements directly)
- RFC 2453 Section 3.6 (the conceptual algorithm this module's docstring calls "a single pass over an advertisement")
