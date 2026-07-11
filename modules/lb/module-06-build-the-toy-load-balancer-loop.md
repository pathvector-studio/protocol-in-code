# Session 06 / Module 06: Build the Toy Load Balancer Loop

## Position

- Track: Load Balancer
- Session: 06
- Site lesson: `pathvector-site/courses/protocols-in-code/lb/module-06/index.html`
- Source file: `src/protocol_in_code/lb/lb_loop.py`
- Walkthrough script: `examples/lb/session_06_walkthrough.py`

## Core Question

Five earlier files each answer one question in isolation — how to pick among backends assumed to be up, and how to know which ones actually are. What does the smallest object look like that filters a live request through health *before* handing it to whichever picking strategy is configured?

## Outcome

By the end of this session, the learner should be able to:

- name every field on `ToyLoadBalancer` and which earlier session's module owns the logic behind it
- trace `route()`'s order of operations and say why filtering by health happens before strategy dispatch, never after
- explain why `RING` rebuilds its ring on every call, and what that costs
- run a scenario through `run_scenario()` and read `trace` as the record of what happened and why

## Read Order

1. Read the module comment above the imports
2. Read `Strategy`
3. Read `ToyLoadBalancer`'s field list top to bottom
4. Read `__post_init__()`
5. Read `_eligible_backends()`
6. Read `route()` — this is the whole track's dispatch point
7. Read `connection_opened()`, `connection_closed()`, `probe_result()`
8. Read `run_scenario()`
9. Run `examples/lb/session_06_walkthrough.py`

## Read It Like Code

```python
ToyLoadBalancer(
    backends,
    strategy,
    vnodes_per_backend,
    clock,
    round_robin_state,
    conn_counts,
    health,
    trace,
)
```

## Parts List

Every field and every function `lb_loop.py` imports was taught by an earlier session in this track. The capstone's only new code is the wiring between them.

| Import | Session that taught it | What it contributes to `ToyLoadBalancer` |
|---|---|---|
| `round_robin.RoundRobinState`, `pick` (as `rr_pick`) | 01 | `round_robin_state`; the `ROUND_ROBIN` branch of `route()` rebuilds a live copy over only the eligible candidates each call. |
| `least_conn.ConnCounts`, `pick` (as `lc_pick`), `connection_opened`, `connection_closed` | 02 | `conn_counts`; the `LEAST_CONN` branch of `route()`, plus the `connection_opened()`/`connection_closed()` methods that keep its counters honest. |
| `hash_pick.pick` (as `hash_pick`) | 03 | Imported but not dispatched to directly — session 03 ends with the problem (`remap_fraction`'s churn) that `ring.py` answers; the import documents the lineage even though `route()`'s strategies are `ROUND_ROBIN`, `LEAST_CONN`, and `RING`. |
| `ring.build_ring`, `pick` (as `ring_pick`) | 04 | The `RING` branch of `route()`; rebuilds the ring over `candidates` — the currently-eligible backends — on every call. |
| `health.BackendHealth`, `HealthState`, `eligible`, `record_probe` | 05 | `health`; `_eligible_backends()` and `probe_result()` are built directly on this session's state machine. |

## Decision Flow

```text
route(client_key):
  candidates = backends filtered through eligible(health[backend].status)
  candidates empty     -> trace "no eligible backends", return None
  strategy ROUND_ROBIN -> rr_pick() over a live RoundRobinState scoped to candidates
  strategy LEAST_CONN  -> lc_pick() over conn_counts, scoped to candidates
  strategy RING        -> build_ring(candidates, vnodes_per_backend), then ring_pick()
  trace the decision, return backend
```

## Reading Lens

The important move in this session is to stop reading each strategy file as a standalone demo and start asking, at every line of `route()`:

- has `client_key` even reached a picking strategy yet, or is it still being filtered by health?
- if a backend just became `DOWN`, does the *next* call to `route()` see it in `candidates`, or does it take another call to notice?
- for `RING` specifically: does a client key's answer change between two calls where nothing about health changed? Why not?

## Toy Model Boundary

`route()`'s `RING` branch rebuilds the entire ring — `build_ring(candidates, vnodes_per_backend)` — on every single call, an `O(vnodes_per_backend * len(backends))` cost paid per request. The source comment calls this out directly: "the toy favors an honest, obviously-correct rebuild over a production-grade incremental ring update. A real load balancer would rebuild the ring only when membership actually changes, not on every request." Beyond that: there is no half-open state or passive health inference (Session 05's boundary applies here too), and there is no connection draining — `connection_closed()` decrements a counter immediately, with no grace period for in-flight requests on a backend that has since gone `DOWN`.

## Code Landmarks

### The module comment

States the whole capstone's thesis in three sentences: the picking strategies each answer "how do you pick," health answers "which ones are actually up," and `ToyLoadBalancer` is where a live request meets both questions at once.

### `route()`'s first two lines

`candidates = self._eligible_backends()` runs before any strategy-specific code at all. Every strategy, without exception, only ever sees backends that passed `eligible()` — a `DOWN` backend cannot be picked by any of the three strategies, because it is filtered out before dispatch, not checked after.

### The `RING` branch's rebuild

`ring = build_ring(candidates, self.vnodes_per_backend)` runs inside `route()` itself, not once at construction time. This is why `RING` affinity holds across repeated calls with unchanged health, but can move a key the instant health changes `candidates` — the ring is rebuilt from a different backend set on the very next call.

### `run_scenario()`

The docstring names the observable difference between strategies directly: with `RING`, "the same `client_key` keeps hitting the same backend across calls until that backend's health takes it out of the eligible set; every other strategy has no such memory and can move a key at any tick."

## Failure Questions

Use the source file to answer these:

1. `route()` calls `self._eligible_backends()` before checking `self.strategy`. What would change about `ROUND_ROBIN`'s behavior if the health filter ran *after* `rr_pick()` selected a backend instead of before?
2. For the `RING` strategy, `route()` builds a fresh `ring` from `candidates` on every call rather than storing one on `self`. What is the exact cost of that rebuild, in terms of `vnodes_per_backend` and `len(backends)`, and where does the source say so directly?
3. `_eligible_backends()` calls `eligible(self.health[backend].status)` for every backend in `self.backends`. Which `BackendHealth` value does `eligible()` exclude, and which two does it allow through?
4. If `probe_result()` is never called for a given backend, what does `self.health[backend].status` remain, and would that backend be included in `candidates`?
5. `route()` returns `None` and appends a trace line when `candidates` is empty. What is the only way for `candidates` to be empty, given that `self.backends` itself never shrinks in this module?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/lb/session_06_walkthrough.py
```

The walkthrough builds four separate `ToyLoadBalancer` instances to isolate each behavior: `ROUND_ROBIN` skipping a backend driven to `DOWN` by three failed probes; `RING` affinity holding across four repeated routes for the same client key, then moving to a different backend only after that key's backend is driven `DOWN`; `LEAST_CONN` routing around an open connection and returning to the freed backend after it closes; a single-backend balancer driven all the way to `DOWN`, where `route()` returns `None`; and a final check that `trace` is non-empty and contains the probe line that recorded the backend going down.

## Done When

The learner can say all of the following without looking at notes:

- "Every field and function in `lb_loop.py` comes from an earlier session — this module only wires them together in `route()`."
- "Health filtering always happens before strategy dispatch, never after — no strategy can pick a DOWN backend because DOWN backends never reach the strategy."
- "RING rebuilds its ring on every call — that's an honest but non-production cost, and it's the reason affinity survives unrelated calls but breaks cleanly the instant a backend goes DOWN."

## References

This module composes the track: Session 01 (round robin), Session 02 (least connections), Session 03 (modulo hashing and its remap cost), Session 04 (consistent hashing), and Session 05 (the health state machine) each contribute one piece; no new external reference applies beyond the ones already cited in those sessions' own docs.
