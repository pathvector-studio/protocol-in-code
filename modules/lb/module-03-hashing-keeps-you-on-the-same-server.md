# Session 03 / Module 03: Hashing Keeps You on the Same Server

## Position

- Track: Load Balancer
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/lb/module-03/index.html`
- Source file: `src/protocol_in_code/lb/hash_pick.py`
- Walkthrough script: `examples/lb/session_03_walkthrough.py`

## Core Question

How do you guarantee the same client lands on the same backend every time, with no state at all — and what does that guarantee cost you when the backend list changes?

## Outcome

By the end of this session, the learner should be able to:

- explain why neither round robin nor least connections can promise session affinity
- trace `pick()` from a client key to a backend in one modulo expression
- state what `remap_fraction` measures and why the number is close to `(n-1)/n`
- explain why this session ends on a problem statement instead of a fix

## Read Order

1. Read the module docstring at the top of the file
2. Read `_hash_int()`
3. Read `pick()`
4. Read `remap_fraction()`
5. Run `examples/lb/session_03_walkthrough.py`

## Read It Like Code

```python
pick(backends, client_key)
remap_fraction(backends_before, backends_after, sample_keys)
```

## Fields That Matter

| Value | Why it matters |
|---|---|
| `client_key` | Whatever identifies "the same client" to the caller — a session ID, an IP, a cache key. `pick()` doesn't care what it means, only that it's stable across calls. |
| `len(backends)` | The divisor in the fold. `pick()` keeps no memory between calls — every guarantee it makes is a consequence of this one number staying fixed. |
| `sample_keys` | The population `remap_fraction` measures churn over. The fraction is only as trustworthy as the sample is representative. |

## Decision Flow

```text
backends is empty                    -> raise ValueError, nothing to pick
otherwise                            -> index = int(sha256(client_key)) % len(backends)
                                         return backends[index]

remap_fraction(before, after, keys)  -> for each key, compare pick(before, key) vs pick(after, key)
                                         return (# that differ) / (# sampled)
```

## Reading Lens

The important move in this session is to stop asking "which backend is best right now" — the question every prior session answered — and start asking:

- does this function keep any state between calls, or is every call self-contained?
- what single number does the fold depend on, and what happens to every key's answer when that number changes by one?
- is `remap_fraction` measuring who *had* to move, or who *happened* to move?

## Toy Model Boundary

`pick()` hashes with `sha256` and reduces with Python's `%`. Real load balancers reach for cheaper, faster hash functions for this exact operation — cryptographic strength buys nothing here, since the only property needed is that similar keys land unpredictably far apart. `sha256` is used in this toy because it is a standard-library one-liner with no external dependency, not because production code would choose it. Separately, and more importantly: `pick()` has no notion of gradual rebalancing, weighted backends, or virtual nodes — it is the plain modulo fold, deliberately, so `remap_fraction` can show its cost in isolation.

## Code Landmarks

### `_hash_int()`

`int(hashlib.sha256(value.encode("utf-8")).hexdigest(), 16)`. One line: hash the key, read the hex digest as a base-16 integer. Everything downstream is arithmetic on this one number.

### `pick()`

`_hash_int(client_key) % len(backends)`, then index into `backends`. Read the module docstring's framing here: "no state required" is both the feature and, two lines later in the docstring, named as the flaw.

### `remap_fraction()`

Calls `pick()` twice per sample key — once against `backends_before`, once against `backends_after` — and counts disagreements. The docstring is explicit about why the fraction is large: `hash(key) % n` and `hash(key) % (n±1)` are unrelated for almost every key, so changing the backend count by one perturbs nearly everyone's remainder, not just the keys that had to move to keep the population balanced.

## Failure Questions

Use the source file to answer these:

1. Which single expression in `pick()` turns a `client_key` string into a `backends` index, and what are its two inputs?
2. Calling `pick(backends, "same-key")` twice with an unchanged `backends` tuple — why must both calls return the same backend? Point to the state (or lack of it) that guarantees this.
3. `remap_fraction` compares `pick(backends_before, key)` against `pick(backends_after, key)` for each key. What exactly counts as "remapped," and what does the function return if `sample_keys` is empty?
4. Growing `backends` from 4 entries to 5 changes the divisor in `pick()`'s modulo from 4 to 5. Why does the docstring say this remaps close to `(n-1)/n` of all keys rather than close to `1/n`?
5. What forward reference does the module docstring make about `ring.py`, and what problem does it say `ring.py` exists to fix?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/lb/session_03_walkthrough.py
```

The walkthrough confirms one key always resolves to the same backend, checks that a handful of different keys spread across multiple backends, and measures the remap fraction when growing a 4-backend set to 5 over 5000 sample keys — landing above 0.5, matching the `(n-1)/n` expectation.

## Done When

The learner can say all of the following without looking at notes:

- "Hashing needs no state at all — the same key always folds onto the same backend as long as the backend count doesn't change."
- "The fold depends on `len(backends)`, so changing that count by one perturbs almost every key's remainder, not just the ones that strictly needed to move."
- "This problem — not a fix for it — is what this session leaves you with. The fix is a ring, and that's the next session's scope."

## References

- No RFC governs backend selection algorithms — this is a load-balancing implementation technique, not a wire protocol.
- As used by memcached client libraries for cache-server selection before consistent hashing became standard (the "modulo hashing" baseline that motivated the technique below).
- Consistent hashing, the fix this session forward-points to: Karger, D. et al., "Consistent Hashing and Random Trees" (STOC 1997) — the classic paper this track's `ring.py` (Session 04) implements a toy version of.
