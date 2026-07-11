# Session 01 / Module 01: Round Robin Is One Index

## Position

- Track: Load Balancer
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/lb/module-01/index.html`
- Source file: `src/protocol_in_code/lb/round_robin.py`
- Walkthrough script: `examples/lb/session_01_walkthrough.py`

## Core Question

How do you spread requests evenly across backends when you are willing to know nothing else about them?

## Outcome

By the end of this session, the learner should be able to:

- state the entire piece of state round robin keeps, in one sentence
- trace `next_index` through a full cycle and explain the wrap
- explain why `pick_weighted` expands the backend list instead of computing a ratio
- name one cost of round robin's blindness that the rest of the track exists to fix

## Read Order

1. Read the module docstring at the top of the file
2. Read `RoundRobinState`
3. Read `pick()`
4. Read `pick_weighted()`
5. Run `examples/lb/session_01_walkthrough.py`

## Read It Like Code

```python
RoundRobinState(
    backends,
    next_index=0,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `backends` | The ring being walked. Order is the only thing that matters here — round robin has no opinion on which backend is "better." |
| `next_index` | The entire state of the algorithm. One integer, nothing else, is enough to remember "whose turn is it." |

## Decision Flow

```text
backends is empty                 -> raise ValueError, nothing to pick
otherwise                          -> hand out backends[next_index % len(backends)]
                                       then next_index = (next_index + 1) % len(backends)
```

## Reading Lens

The important move in this session is to stop looking for a "smart" selection rule and start asking:

- what is the one field this function reads before choosing?
- what is the one field this function writes after choosing?
- what does the modulo operator do at the moment `next_index` reaches `len(backends)`?

## Toy Model Boundary

`pick_weighted` implements weight by literally repeating a backend's name in an expanded tuple — a weight-2 backend appears twice before the index moves on. The docstring calls this "the dumbest honest way," and that framing is the point: it is not the smooth interleaving a production load balancer uses to avoid sending a backend two requests back-to-back, but reading `expanded` shows you the exact proportions before a single request routes anywhere. There is no health awareness, no load awareness, no history beyond the index — that poverty is what every later session in this track pays down.

## Code Landmarks

### `RoundRobinState`

A dataclass holding a tuple and an integer. There is no dict, no timestamp, no counter per backend — the entire session's teaching point lives in how small this is.

### `pick()`

Two lines of real work: index into `backends` with modulo, then advance `next_index` with modulo. Read the modulo twice — once to select, once to wrap. Nothing else in the function has a side effect.

### `pick_weighted()`

Builds `expanded` fresh on every call from `state.backends` and `weights`, then runs the exact same index-and-advance logic as `pick()` against that expanded tuple. Missing weights default to 1. Because `expanded` is rebuilt each call, `state.next_index` is walking a different-length ring than `pick()` would use on the same state — the two functions are not meant to be mixed on one `RoundRobinState`.

## Failure Questions

Use the source file to answer these:

1. `RoundRobinState(backends=("a", "b", "c"))` — after three calls to `pick()`, what is `next_index`, and what does a fourth call return?
2. Which single line in `pick()` decides where in `backends` the wrap happens?
3. For `weights = {"a": 2, "b": 1}` and `backends = ("a", "b")`, what does `expanded` look like, and how many entries does `next_index` cycle through?
4. If `weights` omits a backend entirely, what weight does it get, and where in the source is that decided?
5. `pick()` raises `ValueError` under what single condition, and why does `pick_weighted()` need the same guard?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/lb/session_01_walkthrough.py
```

The walkthrough cycles three backends through four picks to show the wrap, then runs a 2:1 weighted state through two full cycles to show the ratio holding exactly.

## Done When

The learner can say all of the following without looking at notes:

- "Round robin's entire memory is one integer that walks a ring of array positions."
- "Weighted round robin doesn't compute a ratio — it expands the list so the ratio is just how many times a name appears."
- "Round robin never asks whether a backend is healthy or busy, which is exactly the gap the rest of this track fills."

## References

- No RFC governs backend selection algorithms — this is a load-balancing implementation technique, not a wire protocol.
- As used by nginx's default `round-robin` upstream strategy (nginx documentation, "Configuring Load Balancing").
- As used by countless L4/L7 load balancers as the baseline strategy against which every other strategy in this track is compared.
