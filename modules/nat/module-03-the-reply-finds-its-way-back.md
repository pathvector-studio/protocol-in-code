# Session 03 / Module 03: The Reply Finds Its Way Back

## Position

- Track: NAT
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/nat/module-03/index.html`
- Source file: `src/protocol_in_code/nat/table.py`
- Walkthrough script: `examples/nat/session_03_walkthrough.py`

## Core Question

When a reply packet arrives from the internet, how does the router already know where it belongs — and when was that decision actually made?

## Outcome

By the end of this session, the learner should be able to:

- name the two dictionary keys one `insert()` call writes, and what each is for
- explain why the reverse-direction key is computed from `entry.translated`, not `entry.original`
- trace `match()` and say which of its three outcomes a given tuple produces
- explain why `remove()` must delete two keys instead of one

## Read Order

1. Read `NatEntry`
2. Read `ConntrackTable`
3. Read `MatchDirection` and `MatchResult`
4. Read `insert()` and its docstring closely
5. Read `match()`
6. Read `remove()`
7. Run `examples/nat/session_03_walkthrough.py`

## Read It Like Code

```python
NatEntry(
    original,
    translated,
    created_at,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `NatEntry.original` | The tuple exactly as the private host sent it. This is the forward-direction key. |
| `NatEntry.translated` | The tuple after `rewrite.py` ran — what the world outside actually sees. Never used as a key directly; only its reply is. |
| `NatEntry.created_at` | When this mapping was made. Not read by `insert()`/`match()`/`remove()` themselves — it exists for the timeout logic in a later session. |
| `ConntrackTable.entries` | One dict, `FiveTuple -> NatEntry`. Both keys an `insert()` writes point at the *same* `NatEntry` object. |

## Decision Flow

```text
match(table, packet_tuple):
    packet_tuple not in table.entries        -> NoMatch
    packet_tuple == entry.original            -> Forward
    packet_tuple != entry.original (else)      -> Reverse
```

## Reading Lens

The important move in this session is to stop asking "how does the router figure out where the reply goes when it arrives?" — because it doesn't figure anything out at arrival time. Ask instead:

- what two keys did `insert()` write, back when the *outbound* packet was first seen?
- is `reply_tuple(entry.translated)` a lookup, or is it the same pure swap from Session 01, computed once and stored?
- when `match()` returns `Reverse`, what work is left to do — or was all the work already done?

## Toy Model Boundary

Real conntrack keeps a state machine per flow — TCP handshake progress, half-open/established/time-wait, sequence-number tracking for some helpers — and organizes entries with expiry timers and per-protocol timeout policy, not a single flat dict. This file keeps exactly one `entries` mapping and no state beyond the two keys and a timestamp, so the pre-computed-reply trick — the actual thesis of this session — is visible without a state machine competing for attention. Timeout handling belongs to a later file (`timeout.py`) in this track, not to `table.py`.

## Code Landmarks

### `insert()` — read the docstring first, then the two lines of code

```python
table.entries[entry.original] = entry
table.entries[reply_tuple(entry.translated)] = entry
```

This is the whole session. One call to `insert()` writes two adjacent dictionary entries pointing at the same `NatEntry`:

- `entries[entry.original]` — so a retransmit from the same private host, using the same tuple it always used, matches forward.
- `entries[reply_tuple(entry.translated)]` — the reply direction of the *translated* tuple, computed with the exact same `reply_tuple()` from Session 01. This is the key a reply packet arriving from the internet will present. It exists from the moment `insert()` returns, before any reply has ever been seen.

Nothing "learns" the return path when the reply shows up. The lookup that happens on arrival is a plain dict `get()` against a key that was written earlier.

### `match()`

A `dict.get()`, then one equality check. If the packet's tuple equals `entry.original`, it's the same direction the connection started in (`Forward`). Otherwise — because the only other key ever stored points at this same entry — it must be the reply direction (`Reverse`). There is no third possibility once you're past the `None` check.

### `remove()`

Mirrors `insert()` exactly: pops `entry.original` and pops `reply_tuple(entry.translated)`. A mapping is created as a pair of keys and it is torn down as the same pair. `.pop(key, None)` means removing an already-gone key is a no-op, not an error.

## Failure Questions

Use the source file to answer these:

1. After a single `insert()` call, exactly what two `FiveTuple` values are keys in `table.entries`, in terms of `entry.original` and `entry.translated`?
2. Why does the second key use `reply_tuple(entry.translated)` and not `reply_tuple(entry.original)`? What would break if it used the wrong one?
3. Given a tuple that matches a key in `table.entries` but is not equal to `entry.original`, what does `match()` return, and why does it not need a separate check to know that?
4. What does `match()` return for a tuple that was never part of any `insert()` call, and which line of `match()` produces that outcome?
5. Why must `remove()` pop two keys instead of one? What would the table look like after a "half a remove"?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/nat/session_03_walkthrough.py
```

The walkthrough inserts one `NatEntry`, shows the table now holds two keys pointing at the same entry, matches the original tuple `Forward` and the reply of the translated tuple `Reverse`, misses on an unrelated tuple, then removes the entry and confirms both keys are gone.

## Done When

The learner can say all of the following without looking at notes:

- "One `insert()` writes two keys: the original tuple for the forward direction, and the reply of the translated tuple for the reverse direction."
- "The reply path is pre-computed at insert time with `reply_tuple()` — arrival-time `match()` never learns anything, it only looks up."
- "A mapping is created as a pair of keys and removed as the same pair; there is no such thing as removing half of it."

## References

- RFC 2663, Section 4.1 (Traditional NAT — the address/port binding that makes return traffic addressable)
- RFC 4787, Requirement 4 (Mapping Refresh — a binding is a single mapping used for both directions of a flow, not two independently discovered ones)
