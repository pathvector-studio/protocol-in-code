# Session 03 / Module 03: TTL Is a Hop Budget

## Position

- Track: ICMP
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/icmp/module-03/index.html`
- Source file: `src/protocol_in_code/icmp/ttl.py`
- Walkthrough script: `examples/icmp/session_03_walkthrough.py`

## Core Question

Nothing on the network guarantees a packet won't loop forever between routers. What stops it, and who reports back when it doesn't make it?

## Outcome

By the end of this session, the learner should be able to:

- state exactly what a router does to TTL on every hop, in one sentence
- name the single comparison that decides Forwarded versus Expired
- explain what `expire()` builds and what two things it carries
- trace a starting TTL through repeated hops and predict the exact hop count where it expires

## Read Order

1. Read `HopOutcome`
2. Read `decrement_and_decide()`
3. Read `expire()`
4. Run `examples/icmp/session_03_walkthrough.py`

## Read It Like Code

```python
decrement_and_decide(ttl: int) -> tuple[int, HopOutcome]

expire(quoted: QuotedPacket, router_name: str) -> IcmpMessage
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `ttl` (input to `decrement_and_decide`) | The hop budget as it arrives at this router — already decremented by every router before this one. |
| `remaining` | `ttl - 1`, computed once. Every decision in this file is downstream of this one subtraction. |
| `router_name` (in `expire()`) | Identifies which router spent the last hop — it ends up embedded in the `code` string of the resulting message. |
| `quoted` (in `expire()`) | The packet that got killed, carried into the `TIME_EXCEEDED` message exactly as Session 01 described: an error is a packet about a packet. |

## Decision Flow

```text
remaining = ttl - 1
remaining == 0  -> EXPIRED   (this router kills the packet, reports back with expire())
otherwise       -> FORWARDED (this router passes the packet on)
```

## Reading Lens

The important move in this session is to stop thinking of TTL as "a number that goes down" and start asking:

- how many hops does this packet have left *before* this router touches it?
- is the `== 0` branch the one that fires here, or the `otherwise` branch?
- when a packet expires, which router's name ends up in the report, and why would that matter to whoever's troubleshooting?

## Toy Model Boundary

This file is 27 lines, deliberately as small as `src/protocol_in_code/parser/checksum.py` — the point of both is that the core mechanism is a single arithmetic operation, not a subsystem. Real routers also generate ICMP Time Exceeded under rate limiting, so a router that's spending a lot of hops on dying packets doesn't flood the source with reports — this toy model has no such limiting. IPv4 only: IPv6 renames the field Hop Limit, but the decrement-and-compare logic here carries over unchanged in spirit.

## Code Landmarks

### `decrement_and_decide()`

The whole file's logic in three lines: `remaining = ttl - 1`, then one `if remaining == 0`. There's no separate "less than zero" branch — a well-formed router only ever sees `ttl >= 1` arrive, so `remaining` lands at `0` or higher, never negative.

### `expire()`

Builds a `TIME_EXCEEDED` `IcmpMessage` whose `code` is an f-string naming `router_name`, and whose `quoted` is passed straight through. Read this next to Session 01's `validate_message()`: `TIME_EXCEEDED` is in `ERROR_TYPES`, so this message is only valid *because* it carries a quote — `expire()` isn't optional about that, it's structurally required.

## Failure Questions

Use the source file to answer these:

1. What is `remaining` when `decrement_and_decide` is called with `ttl=1`, and which branch does that value hit?
2. Where exactly in the source does the `== 0` comparison live, and what would change if it were `<= 0` instead?
3. Why does `expire()` require a `QuotedPacket` argument at all — what does Session 01 tell you about what happens if you tried to build a `TIME_EXCEEDED` message without one?
4. What two pieces of information does the `code` string in `expire()`'s output carry, and where do they come from?
5. If a packet starts at `ttl=1` and hits exactly one router, does it ever get forwarded? Trace the single call to `decrement_and_decide()` that answers this.

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/icmp/session_03_walkthrough.py
```

The walkthrough decrements a healthy TTL and a dying one, builds a `TIME_EXCEEDED` message with `expire()`, and then loops a TTL of 4 down to expiry to confirm it takes exactly four hops.

## Done When

The learner can say all of the following without looking at notes:

- "Every router does exactly one thing to TTL: subtract one, then check if that hit zero."
- "TIME_EXCEEDED is an error, so by Session 01's rule it must carry a quote — `expire()` has no other option."
- "A packet with TTL `n` survives exactly `n - 1` forwards before the `n`th router expires it."

## References

- RFC 792 (Internet Control Message Protocol)
