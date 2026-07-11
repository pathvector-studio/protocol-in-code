# Session 02 / Module 02: An Offer Is a Proposal with a Deadline

## Position

- Track: DHCP
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/dhcp/module-02/index.html`
- Source file: `src/protocol_in_code/dhcp/offer.py`
- Walkthrough script: `examples/dhcp/session_02_walkthrough.py`

## Core Question

A server that answers a DISCOVER has set an address aside for a client that might never come back. How long does it wait, and how does it find out — without ever hearing directly from the client — that it lost?

## Outcome

By the end of this session, the learner should be able to:

- explain why `Offer` is a proposal and not a promise
- compute staleness from `made_at` and `OFFER_HOLD_SECONDS` without looking at the function body
- state the `offer_is_stale()` boundary condition precisely, including which side of `now == made_at + OFFER_HOLD_SECONDS` is stale
- explain why `accept_offer()` echoes both `server_id` and `ip`, and what that echo does for servers that were not chosen

## Read Order

1. Read `OFFER_HOLD_SECONDS`
2. Read `Offer`
3. Read `make_offer()`
4. Read `offer_is_stale()`
5. Read `accept_offer()`
6. Run `examples/dhcp/session_02_walkthrough.py`

## Read It Like Code

```python
Offer(
    ip,
    lease_seconds,
    server_id,
    made_at,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `ip` | The address the server set aside. This is what gets echoed into `requested_ip` if the client accepts. |
| `lease_seconds` | How long the client gets to keep the address once it actually accepts — separate from, and much longer than, `OFFER_HOLD_SECONDS`. |
| `server_id` | This server's identity. Echoed back by the client so every server on the segment can tell who won. |
| `made_at` | When the offer was made. Staleness is computed from this, not stored as a separate flag. |

## Decision Flow

```text
now <  made_at + OFFER_HOLD_SECONDS   -> offer is live, hold still applies
now >= made_at + OFFER_HOLD_SECONDS   -> offer is stale, pool can reclaim the address
```

## Reading Lens

The important move in this session is to stop reading `accept_offer()` as "the client says yes" and start asking:

- who else, besides the server that made this specific offer, receives the REQUEST that `accept_offer()` produces?
- what does a losing server learn, and how does it learn it, given that `accept_offer()` never mentions "losing servers" at all?
- what is `OFFER_HOLD_SECONDS` protecting — the client, the server, or the address itself?

## Toy Model Boundary

This lesson is mostly a single-server world: one `Offer`, one `accept_offer()` call, one echoed REQUEST. The echo only becomes interesting the moment a second server exists on the same segment — which is exactly why the docstring on `accept_offer()` talks about servers that were "not named." This file does not model multiple competing servers directly (there's no broadcast simulation, no set of listening servers reacting to the echo), but the REQUEST it builds carries everything a second server would need to notice it lost. Real DHCP servers also track offered-but-unconfirmed leases with their own internal timers and may recycle addresses more aggressively under pressure; `OFFER_HOLD_SECONDS` here is a single fixed constant, not a tunable policy.

## Code Landmarks

### `OFFER_HOLD_SECONDS = 30`

A module-level constant, not a field on `Offer`. Every offer from every server uses the same hold window — there's no per-offer override. Session 03's `pool.py` imports this same constant rather than defining its own, which is worth sitting with: the pool's notion of "how long is a hold good for" and the offer's notion of "how long is an offer good for" are the same number because they are, semantically, the same window.

### `offer_is_stale()`

One line: `now >= offer.made_at + OFFER_HOLD_SECONDS`. The comparison is `>=`, not `>` — at the exact instant `now` equals the deadline, the offer is already stale. There is no grace second.

### `accept_offer()`

Builds a `REQUEST` DhcpMessage, but notice what it does *not* take as a parameter: there's no `dest` or `target_server` argument, because — as in Session 01 — this REQUEST is still broadcast. What it does take is the `offer` itself, and it copies exactly two of that offer's fields forward: `server_id` into `server_id`, and `ip` into `requested_ip`. Read the docstring's claim literally: "the echo is the lesson." A client accepting server A's offer produces a message that server B can inspect and immediately know it wasn't named.

## Failure Questions

Use the source file to answer these:

1. Where does `OFFER_HOLD_SECONDS` live, and which other file in this track imports it directly instead of redefining its own constant? Why would duplicating the value instead be a bug waiting to happen?
2. At exactly `now == offer.made_at + OFFER_HOLD_SECONDS`, is the offer stale? Which comparison operator in `offer_is_stale()` decides this, and what would change if it were `>` instead of `>=`?
3. `accept_offer()` copies two fields from `offer` into the REQUEST it builds. Name both, and name the two fields on `DhcpMessage` they land in.
4. `accept_offer()`'s docstring says the REQUEST is "still broadcast." Given what Session 01 established about `DhcpMessage` having no destination field, what in `accept_offer()`'s signature or return value would have to change for this message to be addressed to one specific server instead?
5. `lease_seconds` is a field on `Offer`, but neither `offer_is_stale()` nor `accept_offer()` reads it. What does `lease_seconds` govern instead, and how is that different from what `OFFER_HOLD_SECONDS` governs?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dhcp/session_02_walkthrough.py
```

The walkthrough makes one offer and checks staleness on both sides of the `OFFER_HOLD_SECONDS` boundary, then accepts the offer and asserts that the resulting REQUEST carries both the offering server's `server_id` and its `ip`.

## Done When

The learner can say all of the following without looking at notes:

- "An offer isn't a promise — it's a hold with a deadline, and the deadline is `made_at + OFFER_HOLD_SECONDS`, not a separate expiry field."
- "At `now == made_at + OFFER_HOLD_SECONDS` the offer is already stale, because the comparison is `>=`."
- "`accept_offer()` echoes `server_id` and `ip` into the REQUEST so that every server on the segment — not just the winner — can read the outcome off a message that was never addressed to any of them specifically."

## References

- RFC 2131 Section 3.1 — the OFFER/REQUEST exchange, including the client's selection among multiple offers and the implicit decline this leaves for non-selected servers
