# Session 04 / Module 04: The Cache Answers First

## Position

- Track: DNS
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/dns/module-04/index.html`
- Source file: `src/protocol_in_code/dns/cache.py`
- Walkthrough script: `examples/dns/session_04_walkthrough.py`

## Core Question

Why do most DNS queries never leave the resolver, and what exactly decides hit versus miss?

## Outcome

By the end of this session, the learner should be able to:

- explain why the cache is consulted before any network step
- name the key a cache entry is stored under
- explain why the same name with a different type is a miss
- describe what happens to an entry the moment it expires

## Read Order

1. Read `CacheEntry`
2. Read `ResolverCache`
3. Read `entry_is_expired()`
4. Read `lookup()`
5. Read `store()`
6. Run `examples/dns/session_04_walkthrough.py`

## Read It Like Code

```python
CacheEntry(
    records,
    stored_at,
    ttl,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `records` | The answer being reused. |
| `stored_at` | When the answer arrived. Expiry is computed from this, not stored. |
| `ttl` | How long the authoritative side allowed this answer to be reused. |

## Decision Flow

```text
key not in cache            -> Miss   (go to the network)
entry past stored_at + ttl  -> Expired (delete, then go to the network)
otherwise                   -> Hit    (answer locally)
```

## Reading Lens

The important move in this session is to stop thinking of the cache as an optimization detail and start asking:

- what key was this answer stored under?
- what time did `lookup()` run, relative to `stored_at + ttl`?
- did this query touch the network at all?

## Toy Model Boundary

Real caches store negative answers, partial chains, and per-record TTLs, and they cap TTLs with local policy. This lesson keeps one entry per question key so the hit/miss/expired branching stays readable.

Time is an integer passed in as `now`. Making the clock an argument instead of calling a clock inside is what makes every scenario in the walkthrough reproducible.

## Code Landmarks

### `question_key()` (from Session 01)

The cache key is the question identity from Session 01, unchanged. Different type, different key, different entry.

### `entry_is_expired()`

One comparison: `now >= stored_at + ttl`. Expiry is arithmetic, not a background process.

### `lookup()`

The main reading target. Three outcomes, and the Expired branch also deletes — an expired entry is treated as if it were never there.

### `store()`

A network answer becomes a cache entry stamped with arrival time. Nothing else about the resolver changes.

## Failure Questions

Use the source file to answer these:

1. Why is `lookup()` for `WWW.Example.COM.` a hit after storing `www.example.com`?
2. Why is `lookup()` for the same name with `qtype="AAAA"` a miss?
3. At exactly `now == stored_at + ttl`, is the entry alive or expired? Which comparison decides?
4. After an Expired lookup, what does the very next lookup for the same key return, and why?
5. Why does `lookup()` take `now` as a parameter instead of reading a clock?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dns/session_04_walkthrough.py
```

The walkthrough stores one answer and shows hit, miss, and expiry purely by moving `now`.

## Done When

The learner can say all of the following without looking at notes:

- "The cache is keyed by the full question, so name alone is not enough."
- "Hit, miss, and expired are the only three outcomes, and expired behaves like miss plus a delete."
- "Most queries are answered by arithmetic on `stored_at + ttl`, not by the network."

## References

- RFC 1034 Section 5.3.1
- RFC 1035 Section 7.4
- RFC 2308 Section 5 (caching, including negative caching this toy skips)
