# Session 05 / Module 05: TTL Is a Clock, Not a Config

## Position

- Track: DNS
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/dns/module-05/index.html`
- Source file: `src/protocol_in_code/dns/ttl.py`
- Walkthrough script: `examples/dns/session_05_walkthrough.py`

## Core Question

If a record says TTL 300, what number does a client actually receive two minutes later, and who removes the entry when it hits zero?

## Outcome

By the end of this session, the learner should be able to:

- compute remaining TTL from `stored_at`, `ttl`, and `now`
- explain why a resolver serves a decreasing TTL, not the original one
- explain pruning as a sweep over expiry arithmetic
- describe prefetch/refresh as a threshold on remaining time, not on age

## Read Order

1. Read `remaining_ttl()`
2. Read `served_ttl()`
3. Read `prune_expired()`
4. Read `refresh_needed()`
5. Run `examples/dns/session_05_walkthrough.py`
6. Compute one remaining-TTL value by hand before running it

## Read It Like Code

```python
remaining_ttl(entry, now)
served_ttl(entry, now)
prune_expired(cache, now)
refresh_needed(entry, now, threshold)
```

## Values That Matter

| Value | Why it matters |
|---|---|
| `stored_at + ttl` | The single moment the entry stops being valid. Everything derives from it. |
| `remaining_ttl` | The entry's life left right now. Clamped at zero, never negative. |
| `served_ttl` | What downstream clients receive. Serving the original TTL would let stale data outlive its authority. |
| `threshold` | The refresh trigger. It compares against remaining time, so it fires near expiry regardless of when the entry was stored. |

## Timeline

```text
stored_at            stored_at + ttl
   |---- remaining ----|
   ^ now here: remaining = stored_at + ttl - now
                        ^ now here or later: remaining = 0, entry is prunable
```

## Reading Lens

The important move in this session is to stop reading TTL as a static field in a zone file and start asking:

- what is `now` relative to `stored_at + ttl`?
- which TTL value is this component seeing: original, remaining, or served?
- is expiry enforced at read time, at sweep time, or both?

## Toy Model Boundary

Real resolvers clamp TTLs with minimum and maximum policies, keep per-record (not per-answer) TTLs, and may serve stale data under RFC 8767. This lesson keeps the arithmetic pure so the clock behavior itself is the whole reading target.

`served_ttl()` currently equals `remaining_ttl()`. It exists as a separate function because it is a separate protocol concept — the number handed downstream — and real implementations diverge here.

## Code Landmarks

### `remaining_ttl()`

One `max(0, ...)` expression. The clamp is the difference between "expired" and "negative time", which no protocol field can carry.

### `prune_expired()`

Expiry does not fire an event. Something has to walk the entries and apply the same arithmetic. Note it collects keys first, then deletes.

### `refresh_needed()`

Prefetching before expiry keeps hot names always answerable. The branch is on remaining time — an entry stored long ago with a long TTL does not need refreshing.

## Failure Questions

Use the source file to answer these:

1. What is `remaining_ttl` at exactly `now == stored_at + ttl`?
2. Why must `remaining_ttl` clamp at zero instead of going negative?
3. A client asks twice, 100 seconds apart. Why do the two answers carry different TTLs?
4. In `prune_expired()`, why are keys collected before any deletion happens?
5. Two entries have the same age. One needs refresh, one does not. What differs?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dns/session_05_walkthrough.py
```

The walkthrough slides `now` along one entry's lifetime, then prunes a three-entry cache at a single instant.

## Done When

The learner can say all of the following without looking at notes:

- "TTL is consumed from the moment the answer is stored, not from when it is read."
- "A resolver serves remaining time, so downstream caches can never outlive the original authority."
- "Nothing expires by itself. Reads and sweeps both apply the same arithmetic."

## References

- RFC 1034 Section 3.6
- RFC 1035 Section 3.2.1
- RFC 8767 (serve-stale, the real-world extension this toy skips)
