# Session 04 / Module 04: The Ring Survives a Server Change

## Position

- Track: Load Balancer
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/lb/module-04/index.html`
- Source file: `src/protocol_in_code/lb/ring.py`
- Walkthrough script: `examples/lb/session_04_walkthrough.py`

## Core Question

Session 03 showed that folding a client key onto `len(backends)` with modulo remaps almost every key when membership changes. What has to change about the fold so that only the keys that truly need to move actually move?

## Outcome

By the end of this session, the learner should be able to:

- explain why hashing backends and keys onto the same circle removes `len(backends)` from the fold entirely
- explain why each backend claims many points on the circle instead of one
- trace `pick()` as a binary search over sorted positions, not a new algorithm
- state, with a number, how much smaller the ring's remap cost is than hash-mod's for the same membership change

## Read Order

1. Read the module comment at the top of `ring.py`
2. Read `_hash_int()`
3. Read `build_ring()`
4. Read `pick()`
5. Read `remap_fraction()`
6. Run `examples/lb/session_04_walkthrough.py`

## Read It Like Code

```python
build_ring(
    backends,
    vnodes_per_backend,
) -> ring  # tuple[tuple[int, str], ...], sorted by position

pick(ring, client_key) -> backend
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `ring` entry `(position, backend)` | A single point on the circle. The tuple is sorted by `position`, which is what makes `pick()` a binary search instead of a scan. |
| `vnodes_per_backend` | How many points each backend claims. More points, smoother distribution and smaller remap share per membership change — at the cost of a bigger ring to build and search. |
| `client_key`'s hash | The key's own position on the same circle backends are hashed onto. Never divided by `len(backends)`. |

## Decision Flow

```text
pick(ring, client_key):
  hash client_key onto the circle
  find the first ring position at or after that hash   (bisect_left)
  if that position is past the last point               -> wrap to index 0
  return the backend owning that position
```

## Reading Lens

Session 03 ended with a problem, not a solution: `hash_pick.py`'s `remap_fraction` measured how much churn one membership change causes, and the answer was "almost everyone moves." This session is the answer to that problem. Read `ring.py` against that memory and ask, at every function:

- where did `len(backends)` disappear from the fold?
- what makes `pick()` "IS binary search," in the module comment's own words, rather than an approximation of one?
- when a backend is added or removed, which points on the circle actually change, and which stay exactly where they were?

## Toy Model Boundary

This ring is rebuilt from scratch on every call to `build_ring()` — there is no incremental structure that adds or removes one backend's points without touching the rest. That rebuild is `O(vnodes_per_backend * len(backends))`, cheap enough for this toy's backend counts but not how a production consistent-hash ring is maintained under frequent membership churn (see Session 06's Toy Model Boundary, where `route()` pays this cost on every request). `vnodes_per_backend` is also a single global constant here; real deployments often weight vnode count per backend capacity, which this toy does not model.

## Code Landmarks

### The module comment

States the whole idea before any code: backends and keys share one circle, a key is served by the first backend at or after its position going clockwise, and only the keys between a changed backend and its neighbors move.

### `build_ring()`

Each backend contributes `vnodes_per_backend` points, one per `f"{backend}#{i}"`. The `sorted()` call at the end is what turns "look up my clockwise neighbor" into a data structure that binary search can answer.

### `pick()`

`bisect.bisect_left` on the list of positions is the entire lookup. The wraparound (`if index == len(ring): index = 0`) is the one line that makes the line "circle," not "list."

### `remap_fraction()`

Same signature as `hash_pick.remap_fraction` — same question, built by comparing `pick()` on a before-ring and an after-ring for the same sample keys. The doc string says it outright: "same signature ... much smaller answer."

## Failure Questions

Use the source file to answer these:

1. Why does `build_ring()` hash `vnodes_per_backend` separate points per backend instead of one point per backend?
2. `pick()` calls `bisect.bisect_left`. What does the ring's `sorted()` call in `build_ring()` have to be true for `bisect_left` to return a correct clockwise neighbor?
3. What happens in `pick()` when a key's hash is greater than every position on the ring — which line handles that, and what does it return?
4. `remap_fraction()` builds two full rings (`ring_before`, `ring_after`) rather than diffing the point lists. What would have to be true for a diff-based approach to give the same answer?
5. If `vnodes_per_backend` were 1 instead of 100, what would happen to the fraction of keys that move when one backend is removed, and why does the module comment call this "dumping load onto whichever one neighbor happened to sit next to it"?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/lb/session_04_walkthrough.py
```

The walkthrough checks that the same key always lands on the same backend, then runs the side-by-side headline: on a 4-to-5 backend growth over 5000 sample keys, the ring remaps roughly a fifth of them while `hash_pick.remap_fraction` on the same inputs remaps roughly four-fifths. It closes by removing a backend and asserting that every key that moved was formerly served by the removed backend, and that a key not on the removed backend stays exactly where it was.

## Done When

The learner can say all of the following without looking at notes:

- "The ring never divides by `len(backends)` — backends and keys share one circle, and `pick()` just finds the nearest clockwise point."
- "Virtual nodes exist so that removing one backend spreads its lost keys across many neighbors instead of dumping them all on one."
- "On the same 4-to-5 growth, the ring remaps roughly a fifth of keys where hash-mod remaps roughly four-fifths — that's the whole reason this module exists."

## References

- Karger, D., Lehman, E., Leighton, T., Levine, M., Lewin, D., Panigrahy, R. (1997). "Consistent Hashing and Random Trees: Distributed Caching Protocols for Relieving Hot Spots on the World Wide Web." STOC 1997.
