# Session 01 / Module 01: The Cache Has Moods

## Position

- Track: ARP/ND
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/arp/module-01/index.html`
- Source file: `src/protocol_in_code/arp/cache.py`
- Walkthrough script: `examples/arp/session_01_walkthrough.py`

## Core Question

When an ARP mapping outlives its freshness window, does it disappear, or does it just get less trusted?

## Outcome

By the end of this session, the learner should be able to:

- name the three `NeighborState` values and what each one means about a mapping's trustworthiness
- explain what `lookup()` does to a `REACHABLE` entry that has outlived `REACHABLE_SECONDS`
- state the exact boundary condition that triggers that change, and whether it is inclusive
- explain why a `STALE` entry still returns a MAC address instead of returning nothing

## Read Order

1. Read the module comment at the top of the file
2. Read `NeighborState`
3. Read `NeighborEntry` and `NeighborCache`
4. Read `lookup()`
5. Read `start_resolution()`
6. Read `confirm()`
7. Run `examples/arp/session_01_walkthrough.py`

## Read It Like Code

```python
NeighborEntry(
    mac,
    state,
    updated_at,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `mac` | The answer being cached. `None` while `INCOMPLETE`; always populated once `REACHABLE` or `STALE`. |
| `state` | Not just present-or-absent — a three-way mood: `INCOMPLETE`, `REACHABLE`, `STALE`. |
| `updated_at` | The timestamp `lookup()` measures staleness against. Reset by every `confirm()`. |

## Decision Flow

```text
ip not in cache                                  -> LookupResult(None, None)
entry.state is REACHABLE
  and now - entry.updated_at >= REACHABLE_SECONDS -> mutate entry.state to STALE, then return it (mac included)
otherwise                                         -> return the entry's current state and mac unchanged
```

## Reading Lens

The important move in this session is to stop thinking of a cache entry as "present or expired" and start asking:

- what mood is this entry in right now, and can I still use its MAC?
- what timestamp is `lookup()` comparing `now` against, and is the comparison `>` or `>=`?
- did this lookup just change the entry, or only read it?

This is the direct contrast to `modules/dns/module-04-the-cache-answers-first.md`. That DNS resolver cache expires to **absence**: `entry_is_expired()` returns true, `lookup()` deletes the key, and the very next lookup for that name is a plain `MISS` — as if the entry had never been stored. This neighbor cache expires to a **weaker state** instead. A `REACHABLE` entry that outlives `REACHABLE_SECONDS` is not deleted; `lookup()` mutates it in place to `STALE` and still hands back its MAC. Nothing about the DNS lookup path has an equivalent to `STALE` — DNS has exactly two outcomes for an aged-out entry (alive or gone), while ARP's neighbor cache has three states precisely so it can keep answering while flagging the answer for re-confirmation. Same shape of question — "is this answer still good?" — two different protocols, two different answers to what "no longer good" means.

## Toy Model Boundary

Real IPv6 Neighbor Discovery (RFC 4861 §7.3) has five neighbor states — `INCOMPLETE`, `REACHABLE`, `STALE`, `DELAY`, and `PROBE` — plus a reachability timer that fires from `REACHABLE` on its own, independent of whether anything looks the entry up. This toy has three states and no background timer at all: the `REACHABLE -> STALE` transition only happens the moment something calls `lookup()`, not on a schedule. There is also no retry or timeout for an entry stuck in `INCOMPLETE` — `start_resolution()` sets `mac=None` and nothing in this file ever gives up on it or retries the who-has. IPv4 ARP itself does not have `STALE` as a wire concept; this module borrows ND's shape to make the "degrade, not delete" idea concrete without needing a second protocol's full state machine.

## Code Landmarks

### The module comment

States the whole thesis before any code: this cache has "moods," not just a deadline. Read it first — it explicitly contrasts against `dns/cache.py`.

### `NeighborState`

Three values, not two. `INCOMPLETE` means "resolution in progress, no answer yet." `REACHABLE` and `STALE` both mean "here is an answer," differing only in how much you should trust it without re-confirming.

### `lookup()`

The main reading target. One `if` decides everything: `entry.state is NeighborState.REACHABLE and now - entry.updated_at >= REACHABLE_SECONDS`. Both conditions must hold — an already-`STALE` or `INCOMPLETE` entry is left alone by this check entirely, because only `REACHABLE` entries have a freshness clock that can run out.

### `confirm()`

The only way back to `REACHABLE`. It doesn't matter whether the entry was `STALE`, `INCOMPLETE`, or missing — `confirm()` always writes a brand-new `NeighborEntry` stamped with the current time.

## Failure Questions

Use the source file to answer these:

1. At exactly `now - entry.updated_at == REACHABLE_SECONDS`, does `lookup()` return `REACHABLE` or `STALE`? Which operator in the code decides this?
2. Why does `lookup()` return a MAC address for a `STALE` entry instead of `None`?
3. If an entry is already `STALE` and 500 more seconds pass, what does the next `lookup()` return — does the state change again?
4. What is `entry.mac` immediately after `start_resolution()` runs, and which state is it paired with?
5. Does `lookup()` on an `INCOMPLETE` entry ever change its state? Which line in `lookup()` proves this?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/arp/session_01_walkthrough.py
```

The walkthrough resolves one IP from `INCOMPLETE` to `REACHABLE`, lets it cross the `REACHABLE_SECONDS` boundary to watch it degrade to `STALE` while still returning its MAC, and then confirms it again to show the cache moving back to `REACHABLE`.

## Done When

The learner can say all of the following without looking at notes:

- "A neighbor cache entry has three moods, not two states — INCOMPLETE, REACHABLE, and STALE."
- "REACHABLE degrades to STALE at exactly REACHABLE_SECONDS, in place, and the MAC survives the degrade."
- "Unlike the DNS resolver cache, this cache never deletes an aged-out entry — it just stops trusting it as much."

## References

- RFC 826 (An Ethernet Address Resolution Protocol)
- RFC 4861 Section 7.3 (Neighbor Discovery for IP version 6, Neighbor Unreachability Detection state machine)
