# Session 05 / Module 05: Health Is a State Machine

## Position

- Track: Load Balancer
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/lb/module-05/index.html`
- Source file: `src/protocol_in_code/lb/health.py`
- Walkthrough script: `examples/lb/session_05_walkthrough.py`

## Core Question

None of the picking strategies taught so far know whether a backend is actually answering — only that it exists. What turns a stream of probe results into a routing decision, and why is going down fast and coming back slow the same design, not two different ones?

## Outcome

By the end of this session, the learner should be able to:

- name the three `BackendHealth` states and what each one means for routing
- state the exact probe count at which HEALTHY becomes DOWN, and the exact probe count at which DOWN becomes HEALTHY again
- explain why those two counts are different, and name the asymmetry
- explain why SUSPECT still receives traffic while DOWN does not

## Read Order

1. Read the module comment at the top of `health.py`
2. Read `FAIL_THRESHOLD` and `RISE_THRESHOLD`
3. Read `BackendHealth`
4. Read `HealthState`
5. Read `record_probe()`
6. Read `eligible()`
7. Run `examples/lb/session_05_walkthrough.py`

## Read It Like Code

```python
HealthState(
    status,
    consecutive_failures,
    consecutive_successes,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `status` | One of `HEALTHY`, `SUSPECT`, `DOWN`. The only field `eligible()` looks at. |
| `consecutive_failures` | Reset to 0 on any success. Reaching `FAIL_THRESHOLD` while `SUSPECT` is what triggers `DOWN`. |
| `consecutive_successes` | Reset to 0 on any failure. Reaching `RISE_THRESHOLD` while `SUSPECT` is what triggers `HEALTHY`. |

## Decision Flow

```text
record_probe(state, ok):
  ok is True:
    consecutive_successes += 1, consecutive_failures = 0
    status is DOWN                                    -> SUSPECT
    status is SUSPECT and consecutive_successes >= 2   -> HEALTHY
  ok is False:
    consecutive_failures += 1, consecutive_successes = 0
    status is HEALTHY                                 -> SUSPECT
    status is SUSPECT and consecutive_failures >= 3    -> DOWN
```

## Reading Lens

The important move in this session is to stop reading `record_probe()` as "increment a counter" and start tracing the two thresholds against each other:

- how many consecutive failures does it take to go from HEALTHY to DOWN? Count the transitions, not just the threshold constant.
- how many consecutive successes does it take to go from DOWN back to HEALTHY? Compare that count to the one above.
- why does a single good probe right after `DOWN` land on `SUSPECT`, not `HEALTHY`?

## Toy Model Boundary

This state machine has no notion of *why* a probe failed — timeout, connection refused, and a 500 response all collapse to the same `ok=False`. There is no half-open state that sends a trickle of real traffic to a recovering backend before fully trusting it, and no passive health check that infers failure from live request errors instead of a dedicated probe. `FAIL_THRESHOLD` and `RISE_THRESHOLD` are also fixed constants here, not per-backend or per-probe-interval configuration.

## Code Landmarks

### The module comment

States the layering directly: none of `round_robin.py`, `least_conn.py`, `hash_pick.py`, or `ring.py` know about health at all — `health.py` sits underneath all of them, and `lb_loop.py` filters every strategy's candidates through it before picking.

### `FAIL_THRESHOLD = 3` and `RISE_THRESHOLD = 2`

Two constants, and the entire flap-damping asymmetry lives in the fact that they're different numbers doing structurally different jobs — one counts failures from `SUSPECT`, the other counts successes from `SUSPECT`, but the HEALTHY-to-SUSPECT step on failure has no threshold at all: it's immediate.

### `record_probe()`'s two branches

The `ok` branch and the failure branch are mirror images in structure but not in speed: failure demotes `HEALTHY` to `SUSPECT` on the very first bad probe, with no threshold check. Recovery never skips `SUSPECT` — even `DOWN` to `HEALTHY` must pass through it.

### `eligible()`

One line, one exclusion: `status is not BackendHealth.DOWN`. The docstring calls `SUSPECT` "a warning label, not a quarantine" — the whole reason `SUSPECT` can ever climb back to `HEALTHY` is that it keeps receiving real traffic and real probes.

## Failure Questions

Use the source file to answer these:

1. Why does a single failed probe demote `HEALTHY` straight to `SUSPECT`, with no threshold check at all, while recovery from `DOWN` requires `RISE_THRESHOLD` consecutive successes?
2. At exactly 2 consecutive failures from `SUSPECT`, is the backend `DOWN` yet? At exactly 3? Which line in `record_probe()` decides?
3. After `DOWN`, the very next successful probe moves `status` to `SUSPECT`, not `HEALTHY`. What has to happen on the following probe for `status` to become `HEALTHY`, and what happens instead if that next probe fails?
4. Why does `eligible()` return `True` for `SUSPECT`? What would break about recovery if `SUSPECT` were excluded from routing the same way `DOWN` is?
5. `consecutive_failures` and `consecutive_successes` are both reset to 0 whenever the *other* kind of probe result occurs. Why does a single success in the middle of a failure streak reset the failure count back to 0 rather than just pausing it?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/lb/session_05_walkthrough.py
```

The walkthrough drives one `HealthState` through the full down-and-back cycle: three consecutive failures (checking that `SUSPECT` arrives on the first and `DOWN` only on the third, not the second), then two consecutive successes from `DOWN` (checking that the first success alone lands on `SUSPECT`, not `HEALTHY`, and that `HEALTHY` only returns after the second). It closes by checking `eligible()` against all three states directly.

## Done When

The learner can say all of the following without looking at notes:

- "Going down is immediate — one failed probe is enough to leave HEALTHY. Coming back is not — it takes two consecutive successes and always passes through SUSPECT first."
- "DOWN arrives at exactly the third consecutive failure from SUSPECT, not the first and not the second."
- "SUSPECT still receives traffic; only DOWN is excluded from routing. That's what lets a recovering backend prove itself."

## References

Health checking here is implemented in the style of HAProxy's and nginx's rise/fall probe-count model — no RFC governs application-layer health checking or flap damping; this module's thresholds are a toy version of a pattern common to production load balancers, not a citation of any single specification.
