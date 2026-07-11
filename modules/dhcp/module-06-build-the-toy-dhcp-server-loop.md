# Session 06 / Module 06: Build the Toy DHCP Server Loop

## Position

- Track: DHCP
- Session: 06
- Site lesson: `pathvector-site/courses/protocols-in-code/dhcp/module-06/index.html`
- Source file: `src/protocol_in_code/dhcp/server_loop.py`
- Walkthrough script: `examples/dhcp/session_06_walkthrough.py`

## Core Question

DORA is always described as four steps — Discover, Offer, Request, Ack. What does the server actually have to check, and in what order, to make those four messages come out right every time, including when two servers answer the same DISCOVER?

## Outcome

By the end of this session, the learner should be able to:

- name every field on `ToyDhcpServer` and which earlier session's module it comes from
- trace `on_message()`'s dispatch order and say what runs before any state-changing code
- explain both NAK paths — wrong `server_id` and stale-or-missing offer — and what each one does to the pool
- run `run_dora()` and read its four-message tuple as proof that DORA is a fixed handshake, not "however many messages it takes"

## Read Order

1. Read the module comment above `ToyDhcpServer`
2. Read `ToyDhcpServer`'s field list top to bottom
3. Read `tick()`
4. Read `on_message()` — the dispatch table
5. Read `_on_discover()`
6. Read `_on_request()` — both NAK paths
7. Read `_nak()`
8. Read `run_dora()`
9. Run `examples/dhcp/session_06_walkthrough.py`

## Read It Like Code

```python
ToyDhcpServer(
    pool,
    lease_table,
    server_id,
    clock,
    trace,
    _outstanding_offers,
)
```

## Parts List

Every field and every function `server_loop.py` imports was taught by an earlier session in this track. The capstone's only new code is the wiring between them.

| Import | Session that taught it | What it contributes to `ToyDhcpServer` |
|---|---|---|
| `discover.DhcpMessage`, `MessageType`, `MessageValidity`, `validate_message` | 01 | The wire message every function below reads or builds; `validate_message` is the first thing `on_message()` calls, before any state changes. |
| `leases.LeaseTable`, `grant_lease` | 04 | `lease_table`; `_on_request()` calls `grant_lease()` the moment a REQUEST is accepted — this is where a hold finally becomes a commitment. |
| `offer.Offer`, `make_offer`, `offer_is_stale` | 02 | `_outstanding_offers`; `_on_discover()` builds the `Offer` with `make_offer()`, and `_on_request()` checks `offer_is_stale()` before honoring it. |
| `pool.AddressPool`, `allocate`, `hold`, `next_free` | 03 | `pool`; `_on_discover()` calls `next_free()` then `hold()`, `_on_request()` calls `allocate()` on acceptance. |
| `renewal.py` (T1/T2, `RenewalState`) | 05 | Not imported directly by `server_loop.py` — this session's DORA loop only grants leases; renewal is the next thing a client does after the ACK this module returns, and is out of scope for the loop itself. |

Session 05 (`renewal.py`) has no import line in this table on purpose: `server_loop.py` never calls into it. The capstone wires together discovery, offering, pooling, and granting — everything up through the moment a lease exists. What a client does with that lease afterward (renewal, rebinding) is Session 05's story, not this loop's.

## Decision Flow

```text
on_message(msg):
  1. validate_message(msg)
       not VALID -> trace it, return None                          (stop here, unconditionally)
  2. msg.message_type is DISCOVER -> _on_discover(msg):
       next_free(pool, clock) is None -> trace "pool exhausted", return None (no OFFER, no NAK)
       otherwise -> hold(pool, ip, clock), make_offer(...), remember it, return OFFER
  3. msg.message_type is REQUEST -> _on_request(msg):
       msg.server_id != self.server_id
            -> pop our own outstanding offer if any, release nothing on the pool itself
               (the hold simply times out via OFFER_HOLD_SECONDS), return NAK
       offer is None or offer_is_stale(offer, clock)
            -> return NAK
       otherwise
            -> allocate(pool, offer.ip), grant_lease(...), forget the offer, return ACK
  4. otherwise -> trace "ignored", return None
```

## Reading Lens

The important move in this session is to stop reading DORA as "four message types" and start reading it as one dispatch function, `on_message()`, that never looks at the pool or the lease table until `validate_message()` has already said the message is shaped right. Ask, at every branch:

- which of the four imported modules — `discover`, `offer`, `pool`, `leases` — is doing the actual work on this line, and which earlier session taught it?
- has `self.pool` or `self.lease_table` actually changed yet, or is this still a check?
- if this REQUEST gets a NAK, which of the two NAK paths in `_on_request()` produced it — and does the trace line distinguish them?

The second NAK path deserves particular attention: a REQUEST whose `server_id` doesn't name this server isn't malformed — `validate_message()` already passed it. It means some other server's OFFER won. This server's only remaining job is to notice it lost and let its own hold quietly expire; `_on_request()`'s trace line even narrates it: "lost -> NAK", with a second line if there was a stale offer to note the release. Losing gracefully is as much a part of this loop as winning.

## Toy Model Boundary

This is a single-server, single-subnet model: there is no relay agent, so every message here is modeled as arriving directly, with no `giaddr` and no forwarding across broadcast domains. `DEFAULT_LEASE_SECONDS = 3600` is the only lease length this server ever offers — there is no per-client requested lease time (option 51) and no server policy for granting anything shorter or longer.

There is no `DHCPRELEASE`, `DHCPDECLINE`, or `DHCPINFORM` handling — `on_message()`'s dispatch only recognizes DISCOVER and REQUEST; anything else falls through to the "ignored" trace line and returns `None`. A client that wants to give a lease back early, or refuse an offered address as already-in-use, has no path in this module. And when the wrong-`server_id` NAK path fires, this server does not explicitly call `release()` on the pool — the losing hold simply expires on its own via `offer_is_stale()` and `OFFER_HOLD_SECONDS` the next time anyone checks it; the trace line's "releasing our own hold" describes forgetting the `Offer` from `_outstanding_offers`, not a pool mutation.

## Code Landmarks

### The module comment above `ToyDhcpServer`

States the whole capstone's structure in four sentences: `discover.py` validates shape, `pool.py` finds and holds an address, `offer.py` decides whether a hold is still live, `leases.py` turns a hold into a commitment. The server's own code is just the sequencing.

### `on_message()`'s first statement

`validate_message(msg)` runs before the dispatch `if` even looks at `msg.message_type`. A malformed REQUEST — missing `server_id` — never reaches `_on_request()` at all; it's rejected and traced in one line, the same way DNS's Session 04 lookup checks the cache before anything else runs.

### `_on_discover()`'s `next_free` call

`next_free()` walks the pool skipping both allocated addresses and addresses on hold from someone else's live offer. If it returns `None`, this function returns `None` too — no OFFER and no NAK. Silence is a legitimate DORA outcome: a client that hears nothing back just retries.

### `_on_request()`'s two `if` branches

The wrong-`server_id` branch and the stale-or-missing-offer branch both end in `self._nak(msg)`, but only the first one has anything to pop from `_outstanding_offers` and trace as a release — read the two branches side by side to see they reach the same return type by different paths.

### `run_dora()`

Builds exactly four messages and asserts the type of two of them (`OFFER`, `ACK`) before returning the tuple. The `assert len(result) == 4` a caller can write against this return value is the whole lesson: DORA is a fixed four-step handshake, not "however many messages it takes."

## Failure Questions

Use the source file to answer these:

1. `on_message()` calls `validate_message(msg)` before checking `msg.message_type` at all. What specific check does `validate_message` run for a REQUEST message, and what happens to that REQUEST if it fails?
2. `_on_request()` has two separate conditions that both return a NAK. Name both. Which one pops from `self._outstanding_offers` and traces a release line, and which one does not?
3. In `run_dora()`, what is asserted about `offer_msg` immediately after `server.on_message(discover)` returns — and what would happen to that assertion if the pool were already exhausted?
4. `_on_discover()` calls `hold(self.pool, ip, self.clock)` before building the `Offer` with `make_offer()`. If those two calls were swapped, would `next_free()` on a second, simultaneous DISCOVER still skip this address?
5. `grant_lease()` is only ever called from one place in `server_loop.py`. Which function, and what has already been checked — via `offer_is_stale()` — by the time that call happens?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dhcp/session_06_walkthrough.py
```

The walkthrough builds one `ToyDhcpServer`, runs `run_dora()` for one client and asserts the four returned messages are DISCOVER, OFFER, REQUEST, ACK in order, confirms the lease exists in `lease_table` right after, runs DORA for a second client and confirms it receives a different IP from the first, drives a REQUEST with the wrong `server_id` through `on_message()` directly and checks the NAK plus the released hold, and finally checks `server.trace` is non-empty and contains the line that marks the first grant.

## Done When

The learner can say all of the following without looking at notes:

- "Every field on ToyDhcpServer belongs to an earlier session; this module only wires them together in on_message()."
- "validate_message() runs first, unconditionally — a malformed message never reaches the pool or the lease table."
- "DORA is exactly four messages: DISCOVER, OFFER, REQUEST, ACK — run_dora() returns a 4-tuple you can assert the length of."
- "A REQUEST naming another server's server_id isn't an error — it means this server lost, and its only job left is to let its hold go."

## References

- RFC 2131 Section 3.1 (the DORA exchange: Discover, Offer, Request, Ack, as the four-message client/server allocation sequence)
