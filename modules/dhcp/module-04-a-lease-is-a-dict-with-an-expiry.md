# Session 04 / Module 04: A Lease Is a Dict with an Expiry

## Position

- Track: DHCP
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/dhcp/module-04/index.html`
- Source file: `src/protocol_in_code/dhcp/leases.py`
- Walkthrough script: `examples/dhcp/session_04_walkthrough.py`

## Core Question

A lease table looks nothing like a DNS cache on the wire — so why is the code that manages one identical, line for line, to the code that manages the other three expiring stores this course has already built?

## Outcome

By the end of this session, the learner should be able to:

- name the key a lease is stored under, and why it has to be the MAC and not the IP
- explain why expiry is computed from `granted_at + duration`, not stored as a deadline
- describe what `lookup_lease` does to an entry the instant it finds it expired
- recognize the expiring-dict shape on sight, in any of its four appearances in this course

## Read Order

1. Read the module comment above `LeaseOutcome`
2. Read `Lease`
3. Read `LeaseTable`
4. Read `lease_is_expired()`
5. Read `lookup_lease()`
6. Read `grant_lease()`
7. Run `examples/dhcp/session_04_walkthrough.py`

## Read It Like Code

```python
Lease(
    ip,
    granted_at,
    duration,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `ip` | The address this lease actually grants. Looked up by MAC, not by this. |
| `granted_at` | When the lease began. Expiry is computed from this, not stored. |
| `duration` | How long the server promised this address for, starting at `granted_at`. |

## Decision Flow

```text
mac not in table                    -> Miss    (nothing was ever granted, or it already expired)
now >= granted_at + duration        -> Expired (delete, then behave exactly like Miss)
otherwise                           -> Hit     (return the lease)
```

## Reading Lens

This is the expiring-dict shape's fourth and last appearance in the course, and the module comment above `LeaseOutcome` says so directly. You have read this shape three times already:

- **DNS, Session 04** (`src/protocol_in_code/dns/cache.py`) — a `CacheEntry` keyed by the question, stamped with `stored_at`, expiring against `ttl`.
- **TLS, Session 06** (`src/protocol_in_code/tls/resumption.py`) — a `SessionTicket` keyed by ticket name, expiring against its lifetime.
- **NAT, Session 05** (`src/protocol_in_code/nat/timeout.py`) — a `NatEntry` keyed by the 5-tuple, expiring against an idle timeout.
- **DHCP, Session 04** (here) — a `Lease` keyed by MAC address, expiring against `duration`.

What stays identical across all four: a dict keyed by some identity, a frozen value that carries its own birth time instead of a stored deadline, and exactly one function — the lookup — where expiry is ever checked, deleting the entry on the way out if it's too old. What varies is only the key and what "identity" means for that protocol: a question tuple for DNS, a ticket name for TLS, a 5-tuple for NAT, a MAC address for DHCP. Read `lookup_lease()` next to `lookup()` from DNS Session 04 side by side — the control flow is the same function with different names.

Ask, at every line:

- what identity is this store keyed by, and could two different things collide under it?
- what time did the lookup run, relative to `granted_at + duration`?
- did this lookup just delete something, and would the caller notice if it didn't check the outcome?

## Toy Model Boundary

Real DHCP servers track far more per lease than this: client identifiers distinct from MAC, per-client requested lease times (option 51), a lease's renewal history, and static reservations that never expire at all. This module keeps one `Lease` per MAC with a single server-chosen `duration`, so the hit/miss/expired branching stays the whole reading target.

There is no `DHCPRELEASE` or `DHCPDECLINE` handling here — a lease only ever ends by running out the clock, never by a client giving it back early or refusing it. That is Session 05 and Session 06 territory to gesture at, not this one's job to model.

## Code Landmarks

### The module comment above `LeaseOutcome`

Names all three prior appearances of this shape by file path and says outright that this is the fourth and last. Read it before reading a single class — it tells you what to expect from the rest of the file.

### `lease_is_expired()`

One comparison: `now >= lease.granted_at + lease.duration`. Same arithmetic as DNS's `entry_is_expired()`, same arithmetic as NAT's idle-timeout check. Expiry is arithmetic, not a background sweep.

### `lookup_lease()`

The main reading target, and the fourth time this course has written this exact function shape. Three outcomes, and the Expired branch deletes from `table.leases` before returning — an expired lease behaves as if it were never granted.

### `grant_lease()`

A REQUEST becomes a lease stamped with the moment it was granted — same move as DNS's `store()` stamping a network answer with `stored_at`. Nothing else about the table changes; overwriting an existing MAC's entry silently replaces any prior lease.

## Failure Questions

Use the source file to answer these:

1. `lookup_lease` takes `mac`, not `ip`. If two different MAC addresses were ever granted the same IP by mistake, would `lookup_lease` be able to tell?
2. At exactly `now == granted_at + duration`, is the lease alive or expired? Which operator in `lease_is_expired` decides — is it `>` or `>=`?
3. After an Expired outcome, what does the very next `lookup_lease` call for the same MAC return, and why — what changed inside `table.leases` on the Expired call?
4. `Lease` is a frozen dataclass. When `grant_lease` is called twice for the same MAC, does the second call mutate the first `Lease` object, or produce a new one?
5. Where in `leases.py` is a clock ever read directly, and what does the absence of one tell you about how `now` has to reach `lookup_lease`?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dhcp/session_04_walkthrough.py
```

The walkthrough grants one lease and shows hit, expiry, and the post-expiry miss purely by moving `now`, then names this as the fourth appearance of the expiring-dict shape.

## Done When

The learner can say all of the following without looking at notes:

- "A lease is keyed by MAC, stamped with `granted_at`, and expiry is computed at lookup time from `granted_at + duration` — nothing stores a deadline."
- "This is the same shape as the DNS cache, the TLS ticket store, and the NAT conntrack table — a dict keyed by identity, checked and swept in one function."
- "Expired behaves exactly like Miss, plus a delete — the next lookup for that MAC never sees the stale entry."

## References

- RFC 2131 Section 3.1 (lease lifecycle: a lease is granted for a finite duration and must eventually be renewed or it lapses)
- RFC 2131 Section 4.4.5 (renewal timers T1/T2, previewed here and built in Session 05)
