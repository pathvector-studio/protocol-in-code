# Session 02 / Module 02: Least Connections Is a Counter

## Position

- Track: Load Balancer
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/lb/module-02/index.html`
- Source file: `src/protocol_in_code/lb/least_conn.py`
- Walkthrough script: `examples/lb/session_02_walkthrough.py`

## Core Question

If you're willing to track one number per backend, what does that number buy you that round robin's blind index can't?

## Outcome

By the end of this session, the learner should be able to:

- name the one integer least connections tracks per backend, and what it counts
- explain why `pick()` breaks ties on backend name instead of dict order
- trace how `connection_opened` and `connection_closed` change the outcome of the next `pick()`
- explain why `connection_closed` floors at zero instead of letting the count go negative

## Read Order

1. Read the module docstring at the top of the file
2. Read `ConnCounts`
3. Read `pick()`
4. Read `connection_opened()`
5. Read `connection_closed()`
6. Run `examples/lb/session_02_walkthrough.py`

## Read It Like Code

```python
ConnCounts(
    active: dict[str, int],
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `active` | One count per backend: requests currently in flight there. This is the state round robin got to skip entirely. |

## Decision Flow

```text
backends is empty                          -> raise ValueError, nothing to pick
otherwise                                   -> pick min by (active.get(backend, 0), backend)
                                                ties break on backend name, ascending
connection_opened(backend)                  -> active[backend] += 1 (starts from 0 if unseen)
connection_closed(backend)                  -> active[backend] = max(0, active[backend] - 1)
```

## Reading Lens

The important move in this session is to stop asking "which backend is next in line" and start asking:

- what does `counts.active` look like right now, for every backend?
- if two backends are tied on count, which name wins, and where in the source is that decided?
- did the most recent `pick()` change `counts.active`, or only read it?

## Toy Model Boundary

`pick()` only reads `counts.active` — it never writes to it. The caller is responsible for calling `connection_opened()` once a request is actually routed, and `connection_closed()` once it finishes. This lesson assumes the load balancer reliably sees every close: a request that hangs forever, or a backend that crashes without the LB noticing, leaves a stale count inflated forever. A real load balancer would pair this with timeouts or health checks (see `health.py`, outside this session's scope) to recover from that; this toy keeps the counter itself the whole reading target.

## Code Landmarks

### `ConnCounts`

A dataclass wrapping a single dict, defaulted with `field(default_factory=dict)` so each instance gets its own dict instead of sharing one across calls.

### `pick()`

One `min()` call with a tuple key: `(counts.active.get(backend, 0), backend)`. The docstring is explicit about why the second tuple element exists — without it, ties would resolve however `backends` happens to be ordered, which is deterministic but arbitrary. Sorting on `(count, name)` makes the tiebreak deterministic and documented instead.

### `connection_opened()`

`active.get(backend, 0) + 1`, written back into the dict. A backend with no entry yet is treated as having zero active connections, not as an error.

### `connection_closed()`

`max(0, current - 1)`. Read the comment on the floor: without it, a stray `connection_closed` call for a backend the load balancer had lost track of (say, after a restart wiped `active`) could push a count negative and make that backend look artificially attractive to `pick()` forever after.

## Failure Questions

Use the source file to answer these:

1. With `backends = ("s3", "s1", "s2")` and `counts.active` empty, what does `pick()` return, and which line of `pick()` makes the answer independent of the order of `backends`?
2. What is the exact tuple `pick()` sorts by, and what does the second element of that tuple accomplish?
3. After `connection_opened(counts, "s1")` is called twice and nothing else changes, what does `counts.active` contain, and would `pick()` still return `"s1"` against `("s1", "s2")`?
4. If `connection_closed(counts, "s4")` is called for a backend never seen by `connection_opened`, what does `counts.active["s4"]` become, and which line prevents it from going negative?
5. Given identical `counts` and `backends`, does calling `pick()` twice in a row change its own answer the second time? Which function would have to run in between to change the answer?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/lb/session_02_walkthrough.py
```

The walkthrough starts from an all-zero counter (showing the alphabetical tiebreak), opens and closes connections to move the pick around, and finishes by asserting that identical state produces identical picks.

## Done When

The learner can say all of the following without looking at notes:

- "Least connections needs exactly one integer per backend — how many requests are in flight there right now."
- "Ties don't resolve by accident; `pick()` sorts on `(count, name)` so the tiebreak is a decision, not an artifact of dict order."
- "The counter is only as honest as the calls to `connection_opened` and `connection_closed` — `pick()` itself never updates it."

## References

- No RFC governs backend selection algorithms — this is a load-balancing implementation technique, not a wire protocol.
- As used by nginx's `least_conn` upstream directive (nginx documentation, "Configuring Load Balancing").
- As used by HAProxy's `leastconn` balance algorithm (HAProxy documentation).
