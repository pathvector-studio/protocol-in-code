# Session 03 / Module 03: The Pool Hands Out What's Free

## Position

- Track: DHCP
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/dhcp/module-03/index.html`
- Source file: `src/protocol_in_code/dhcp/pool.py`
- Walkthrough script: `examples/dhcp/session_03_walkthrough.py`

## Core Question

A server has a whole /24 to hand out addresses from. How does it decide which address is next, and how does it avoid handing the same address to two clients at once while an offer is still pending?

## Outcome

By the end of this session, the learner should be able to:

- state what `next_free()` skips over, in order, and why
- explain the difference between `allocated` and `on_hold`, and why they are two separate containers instead of one
- explain why `next_free()` imports `OFFER_HOLD_SECONDS` from `offer.py` instead of defining its own hold duration
- walk through what happens to a held-but-never-allocated address once its hold window closes

## Read Order

1. Read `CANDIDATE_START` and `CANDIDATE_END`
2. Read `PoolOutcome`
3. Read `AddressPool`
4. Read `_candidates()`
5. Read `next_free()`
6. Read `hold()`, `allocate()`, `release()`
7. Run `examples/dhcp/session_03_walkthrough.py`

## Read It Like Code

```python
AddressPool(
    network_prefix,
    allocated: set[str] = set(),
    on_hold: dict[str, int] = {},
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `network_prefix` | The first three octets of the /24. Every candidate address is built by appending a host number to this. |
| `allocated` | A set of addresses with a confirmed lease. Permanent until `release()`. |
| `on_hold` | A dict mapping address to the time its hold *began* — not when it expires. Expiry is computed, exactly like `offer_is_stale()` in Session 02. |

## Decision Flow

```text
ip in pool.allocated                                  -> skip, try next candidate
ip in pool.on_hold and now < held_at + OFFER_HOLD_SECONDS -> skip, try next candidate
otherwise                                              -> return ip
(ran out of candidates)                                -> return None  (POOL_EXHAUSTED)
```

## Reading Lens

The important move in this session is to stop reading `next_free()` as "find an empty slot" and start asking:

- what two separate reasons can make an address unavailable, and which one is permanent?
- `on_hold` stores a start time, not an expiry time — where does the actual expiry math happen, and does it match Session 02's math?
- what does the *order* of candidates guarantee, and what would break if `_candidates()` returned them in a different order each call?

## Toy Model Boundary

`CANDIDATE_START = 10` and `CANDIDATE_END = 50` carve out a visible, human-countable 41-address slice (`.10` through `.50`) of a /24 that actually has 254 usable host addresses. That visibility is deliberate — you can enumerate the whole candidate space in your head, which is the point of a toy model. Real DHCP server implementations track much larger ranges (often the full usable range of a subnet, sometimes multiple pools per subnet) using bitmaps, interval trees, or database-backed range queries instead of a linear scan with `continue` statements, because a linear scan over tens of thousands of candidates on every allocation would not scale. `next_free()`'s O(pool size) walk is the right complexity for a lesson and the wrong complexity for a production allocator — that trade is worth naming, not hiding.

## Code Landmarks

### `_candidates()`

Builds the full range fresh on every call, in ascending host-number order, by string-formatting `network_prefix` and each integer from `CANDIDATE_START` to `CANDIDATE_END` inclusive. Nothing is cached — the "pool" isn't a stored list, it's this function plus whatever `allocated` and `on_hold` currently exclude.

### `next_free()`

Two independent skip conditions, checked in sequence for each candidate: first `ip in pool.allocated` (a flat set membership check), then a hold check that reads `pool.on_hold.get(ip)` and compares against `held_at + OFFER_HOLD_SECONDS` — the same constant, the same `>=`-flavored boundary logic as `offer_is_stale()` in `offer.py`, just written here as `now < held_at + OFFER_HOLD_SECONDS` (skip) rather than `now >= made_at + OFFER_HOLD_SECONDS` (stale). They are the same boundary, phrased from opposite sides. The function returns the first candidate that clears both checks, or `None` if the whole range is exhausted — note there's no `PoolOutcome` value actually constructed here; `next_free()` returns a bare `str | None`, and `PoolOutcome.POOL_EXHAUSTED` exists as a named outcome for callers to map `None` onto, not as something this function produces itself.

### `hold()`, `allocate()`, `release()`

Three small state transitions. `hold()` only ever writes to `on_hold` — it stamps the *current* time, not a future expiry. `allocate()` writes to `allocated` and also pops the address out of `on_hold` if it was there, so an allocated address can never simultaneously look held. `release()` is the inverse of both: it discards from `allocated` and pops from `on_hold`, unconditionally, so releasing an address that was never allocated (or never held) is a safe no-op rather than an error.

## Failure Questions

Use the source file to answer these:

1. `next_free()` does not define its own hold-duration constant. Which file does `OFFER_HOLD_SECONDS` actually live in, and why does reusing that same constant here (rather than picking a new number for the pool) matter for correctness?
2. `on_hold` stores the time a hold *began*, not when it expires. Where in `pool.py` is the expiry actually computed, and what would change if `on_hold` stored expiry times directly instead?
3. `allocate()` calls `pool.on_hold.pop(ip, None)` even though the address might never have had a hold. Why does it use `.pop(ip, None)` instead of `del pool.on_hold[ip]`, and what would happen at runtime if it used `del` on an address with no hold?
4. Two addresses, `.10` and `.11`, are both in `on_hold` — `.10` held at `now=0` and `.11` held at `now=5`. At `now=30`, which one (if either) does `next_free()` skip, and which does it return? Walk through the boundary comparison for both.
5. If every address from `CANDIDATE_START` to `CANDIDATE_END` is in `pool.allocated`, what does `next_free()` return, and what has to happen (in terms of calls to the functions in this file) before it can return a real address again?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dhcp/session_03_walkthrough.py
```

The walkthrough asks for the first free address (`.10`), holds it and watches `next_free()` skip to `.11`, moves `now` past the hold window to show `.10` becomes free again, allocates `.10` to show that removal is permanent regardless of `now`, releases it to show the address returns to the pool, and finally fills the entire candidate range to show exhaustion returns `None`.

## Done When

The learner can say all of the following without looking at notes:

- "`next_free()` skips an address for one of two reasons — it's allocated (permanent) or it's on hold and the hold hasn't expired yet (temporary) — and only the second one is time-dependent."
- "`on_hold` stores when a hold started, and `next_free()` computes whether it has expired using the exact same `OFFER_HOLD_SECONDS` constant that `offer_is_stale()` uses in Session 02 — the pool and the offer agree on what 'expired' means because they share the constant, not because they duplicate the logic."
- "The candidate range is a visible 41 addresses on purpose; a real allocator manages far more addresses with a data structure built for that scale, not a linear scan."

## References

- RFC 2131 Section 4.3 — server behavior on receiving DHCP messages, including the address allocation discussion this toy's `hold`/`allocate`/`release` trio simplifies
