# Session 05 / Module 05: State Expires, Again

## Position

- Track: NAT
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/nat/module-05/index.html`
- Source file: `src/protocol_in_code/nat/timeout.py`
- Walkthrough script: `examples/nat/session_05_walkthrough.py`

## Core Question

A conntrack entry has no close signal from the network most of the time — so what decides it is dead, and why does that decision take ten times longer for TCP than for UDP?

## Outcome

By the end of this session, the learner should be able to:

- state the TCP and UDP expiry limits and explain the 10x asymmetry between them
- trace `is_expired()`'s comparison and say what happens at the exact boundary
- explain why `sweep()` must remove two dictionary keys per expired entry, not one
- explain what `touch()` does to an entry, and why the caller has to re-insert the result

## Read Order

1. Read the module comment above `EXPIRY_SECONDS` — this is the course's fourth expiring-dict
2. Read `EXPIRY_SECONDS`
3. Read `is_expired()`
4. Read `touch()`
5. Read `sweep()`
6. Run `examples/nat/session_05_walkthrough.py`

## Read It Like Code

```python
is_expired(entry, now)
touch(entry, now)
sweep(table, now)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `entry.created_at` | The timestamp expiry is measured from. `touch()` is the only thing that moves it forward. |
| `EXPIRY_SECONDS["tcp"]` | 300 seconds. TCP has an explicit close (FIN/RST), so an idle established connection can still be trusted for minutes. |
| `EXPIRY_SECONDS["udp"]` | 30 seconds. UDP has no close signal at all — the table has to guess a flow is over just because it went quiet. |

## Decision Flow

```text
is_expired(entry, now):
  limit = EXPIRY_SECONDS[entry.original.protocol]
  now >= entry.created_at + limit  -> True  (expired)
  otherwise                        -> False (alive)

sweep(table, now):
  for every entry where is_expired(entry, now):
    delete table[entry.original]
    delete table[reply_tuple(entry.translated)]
  return the original tuples that were removed
```

## Reading Lens

The important move in this session is to recognize the shape you have now seen four times — `src/protocol_in_code/dns/cache.py` (records expire by TTL), `src/protocol_in_code/tls/resumption.py` (tickets expire by lifetime), and now a conntrack entry stamped with `created_at` and checked against a limit at read time — and then ask what is different here:

- which protocol is this entry for, and does that change the limit `is_expired()` reads?
- is this entry being checked (`is_expired`), refreshed (`touch`), or removed (`sweep`) right now?
- if this entry disappears from the table, does *either* endpoint know yet?

That last question is the twist this session adds to the shape: a DNS cache entry or TLS ticket expiring inconveniences one side, which just re-asks or re-negotiates. A NAT mapping expiring silently breaks a flow that neither side chose to close — an idle UDP mapping dying is hole-punching in reverse. No FIN, no RST, nobody asked for this. The next packet from the far side arrives to a table that says `NO_MATCH`, and gets dropped as if it were unsolicited. This is exactly why NAT-traversal techniques (STUN, and application-level keepalives) exist: something has to send traffic often enough to keep `touch()` running before the 30-second UDP clock runs out.

## Toy Model Boundary

Real conntrack (e.g., Linux `nf_conntrack`) tracks TCP state far more granularly than one flat 300-second number — `ESTABLISHED`, `FIN_WAIT`, `TIME_WAIT`, and others each carry their own timeout, and an established connection with keepalives can be trusted for hours or days, not a fixed five minutes. This module collapses all of that to one `EXPIRY_SECONDS["tcp"]` value and one `EXPIRY_SECONDS["udp"]` value, keyed only by protocol, so the read/refresh/sweep arithmetic stays the whole reading target. There is also no half-open or half-closed handling — `is_expired()` cannot see whether a TCP flow ever completed its close, only how long it has been idle.

## Code Landmarks

### The module comment above `EXPIRY_SECONDS`

Names the shape directly and points at the other three appearances in the course. Read this before anything else in the file — it is the frame the rest of the session hangs on.

### `is_expired()`

One comparison, `now >= entry.created_at + limit`, identical in shape to `dns/cache.py`'s `entry_is_expired()`. The only new thing is `limit` itself is looked up per protocol instead of being fixed.

### `touch()`

Returns a **new** frozen `NatEntry` with `created_at` reset to `now` — it does not mutate the entry passed in. The docstring says it plainly: "frozen in, frozen out, so the caller re-inserts the new one." `nat_loop.py`'s `outbound()` and `inbound()` are exactly that caller.

### `sweep()`

Removes **both** keys the entry lives under — `entry.original` and `reply_tuple(entry.translated)` — because `table.py`'s `insert()` put the same entry under both keys in the first place (Session 03). Deleting only one would leave a dangling half-entry that `match()` could still hit.

## Failure Questions

Use the source file to answer these:

1. A TCP entry has `created_at = 100`. At `now = 400`, is it expired? Which line in `is_expired()` decides, and what is the exact boundary value of `now` where the answer flips?
2. `sweep()` deletes `table.entries[entry.original]` and `table.entries[reply_tuple(entry.translated)]`. Why two keys instead of one — what would happen to a later inbound reply packet if `sweep()` only deleted `entry.original`?
3. `touch()` returns a new `NatEntry` instead of modifying the one passed in. What field does it replace, and what stays identical between the input and the output?
4. `EXPIRY_SECONDS["udp"]` is 30 seconds, ten times shorter than `EXPIRY_SECONDS["tcp"]`'s 300. What protocol-level fact about TCP justifies trusting an idle entry for longer?
5. After `sweep()` removes an entry, what does the very next `match()` call against that entry's original tuple return, and why?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/nat/session_05_walkthrough.py
```

The walkthrough builds one TCP and one UDP entry, shows the TCP entry alive at 299 seconds and expired at exactly 300, shows the UDP entry expired at exactly 30 — the 10x asymmetry side by side — inserts both into a table and confirms `sweep()` removes both keys per entry and reports what it removed, then shows `touch()` resetting an entry's clock so it survives past the deadline it would otherwise have missed.

## Done When

The learner can say all of the following without looking at notes:

- "This is the fourth expiring-dict in the course — stamp the value with a creation time, compare age to a limit at read time."
- "TCP gets 300 seconds because it has an explicit close; UDP gets 30 because it has none — the table has to guess."
- "sweep() must delete two keys per entry, because insert() put the entry under two keys. touch() replaces created_at and returns a new entry the caller has to re-insert."
- "An idle UDP mapping dying breaks a flow that nobody asked to close — that's the NAT-traversal and keepalive problem in one sentence."

## References

- RFC 4787 (NAT UDP Behavioral Requirements — mapping timeout recommendations for UDP)
- RFC 5382 (NAT TCP Requirements — TCP connection timeout behavior for NAT)
