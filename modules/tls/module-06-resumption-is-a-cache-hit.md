# Session 06 / Module 06: Resumption Is a Cache Hit

## Position

- Track: TLS
- Session: 06
- Site lesson: `pathvector-site/courses/protocols-in-code/tls/module-06/index.html`
- Source file: `src/protocol_in_code/tls/resumption.py`
- Walkthrough script: `examples/tls/session_06_walkthrough.py`

## Core Question

A full handshake is expensive. What exactly does a session ticket let a client skip, and what decides whether a stored ticket is still good?

## Outcome

By the end of this session, the learner should be able to:

- name the key a session ticket is stored under
- state the single comparison that decides expiry
- describe what happens to a ticket the moment it's found expired
- explain, precisely, why this module's shape is the DNS cache's shape again

## Read Order

1. Read `SessionTicket`
2. Read `TicketStore`
3. Read `ticket_is_expired()`
4. Read `lookup_ticket()`
5. Read `issue_ticket()`
6. Run `examples/tls/session_06_walkthrough.py`

## Read It Like Code

```python
SessionTicket(
    master_secret,
    cipher_suite,
    issued_at,
    lifetime,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `master_secret` | The cryptographic material a resumed handshake reuses instead of re-deriving. This is the thing the whole mechanism exists to cache. |
| `cipher_suite` | Pinned at issue time — resumption reuses the suite the original handshake negotiated. |
| `issued_at` | When the ticket was handed to the client. Expiry is computed from this, not stored as a fixed timestamp. |
| `lifetime` | How long the server is willing to honor this ticket. |

## Decision Flow

```text
name not in store               -> Miss   (do a full handshake)
now >= issued_at + lifetime     -> Expired (delete, then do a full handshake)
otherwise                       -> Hit    (resume with master_secret)
```

## Reading Lens

You have seen this exact shape before, in the DNS track's Session 04 (`the cache answers first`, `src/protocol_in_code/dns/cache.py`). Put the two lookup functions side by side and the parallel is not a metaphor — it is the same code:

- `ResolverCache.entries` and `TicketStore.tickets` are both `dict[str, ...]` keyed by a single identity string.
- `entry_is_expired()` and `ticket_is_expired()` are both one comparison against `stored_at + ttl` / `issued_at + lifetime`.
- `lookup()` and `lookup_ticket()` both return the same three-way outcome — hit, miss, expired — and both **delete on expiry**, so the next lookup for that key is a plain miss, not a repeated "expired."

The lesson here is not "session tickets are like a cache." It's that resolvers and TLS servers independently arrived at the identical data shape — a name-keyed store, a stamped arrival time, an additive lifetime — because it's the natural shape for "avoid redoing expensive work, but not forever." Once you've internalized `lookup()` from the DNS track, `lookup_ticket()` has nothing new to teach you structurally; only the payload (`master_secret` + `cipher_suite` instead of `records`) is different.

## Toy Model Boundary

Real TLS 1.3 resumption includes a PSK binder that cryptographically ties the resumed handshake to the original ticket (so a stolen ticket alone isn't enough), and 0-RTT early data with its own replay-protection concerns. Neither exists here: `issue_ticket()` and `lookup_ticket()` model only the store/expire/reuse lifecycle, not the handshake cryptography that makes resumption safe to use over the wire.

Time is an abstract integer tick passed as `now`, exactly like the DNS cache — there is no wall clock inside `ticket_is_expired()`.

## Code Landmarks

### `ticket_is_expired()`

```python
def ticket_is_expired(ticket: SessionTicket, now: int) -> bool:
    return now >= ticket.issued_at + ticket.lifetime
```

One comparison, `>=`. At `now == issued_at + lifetime` exactly, the ticket is already expired — the boundary tick belongs to `Expired`, not `Hit`.

### `lookup_ticket()`

```python
ticket = store.tickets.get(name)
if ticket is None:
    return TicketLookup(TicketOutcome.MISS, None)

if ticket_is_expired(ticket, now):
    del store.tickets[name]
    return TicketLookup(TicketOutcome.EXPIRED, None)

return TicketLookup(TicketOutcome.HIT, ticket)
```

Three outcomes, same order as the DNS cache: not-present first, then expiry (with a deletion side effect), then hit. The `del` is what makes the *next* lookup for the same name a `MISS` rather than another `EXPIRED`.

### `issue_ticket()`

Stamps `issued_at=now` and writes straight into `store.tickets[name]`, silently overwriting any prior ticket for that name. Nothing here validates that a handshake actually completed — the function models "a completed handshake earns a ticket," but enforcing that a handshake happened first is the caller's responsibility, not this function's.

## Failure Questions

Use the source file to answer these:

1. At exactly `now == issued_at + lifetime`, is the ticket a `HIT` or an `EXPIRED`? Which operator in `ticket_is_expired()` decides it?
2. After a `lookup_ticket()` call returns `EXPIRED`, what does the very next `lookup_ticket()` call for the same name return, and which line makes that happen?
3. Compare `ticket_is_expired()` to the DNS track's `entry_is_expired()` — is the comparison operator the same, and are the field names that feed it (`issued_at`/`lifetime` vs `stored_at`/`ttl`) structurally interchangeable?
4. If you call `issue_ticket()` twice for the same `name` before the first ticket expires, what happens to the first ticket — is it kept alongside the second, or gone?
5. Does `lookup_ticket()` or `issue_ticket()` ever inspect `cipher_suite` or `master_secret` for validity? What does that tell you about what layer is responsible for verifying the ticket is cryptographically sound?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tls/session_06_walkthrough.py
```

The walkthrough mirrors the DNS Session 04 walkthrough's rhythm deliberately: an empty-store miss, an issue followed by a hit that carries the `master_secret` through intact, a hit one tick before the boundary, an expiry at exactly `issued_at + lifetime`, and a miss on the very next lookup proving the expired ticket was deleted, not just marked.

## Done When

The learner can say all of the following without looking at notes:

- "Hit, miss, and expired are the only three outcomes, and expired behaves like miss plus a delete — same as the DNS cache."
- "The boundary tick, `now == issued_at + lifetime`, belongs to expired, not hit."
- "This module and the DNS cache module are the same shape: name-keyed store, stamped arrival time, additive lifetime."
- "Resumption's safety depends on the PSK binder this toy model doesn't implement — this code only models the store/expire/reuse lifecycle."

## References

- RFC 8446 Section 4.6.1 (NewSessionTicket message)
- RFC 8446 Section 2.2 (Resumption and Pre-Shared Key (PSK))
