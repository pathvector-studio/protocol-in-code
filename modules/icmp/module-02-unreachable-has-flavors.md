# Session 02 / Module 02: Unreachable Has Flavors

## Position

- Track: ICMP
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/icmp/module-02/index.html`
- Source file: `src/protocol_in_code/icmp/unreachable.py`
- Walkthrough script: `examples/icmp/session_02_walkthrough.py`

## Core Question

"Destination Unreachable" sounds like one failure. Why does it split into four codes, and why does the sender of the message change depending on which one you get?

## Outcome

By the end of this session, the learner should be able to:

- name the sender implied by each of the four `UnreachableCode` values
- explain why port-unreachable is a different *kind* of failure from net/host-unreachable, not just a different degree
- describe what `next_hop_mtu` in a frag-needed message is for
- build a valid port-unreachable message from a quote and confirm the quote round-trips unchanged

## Read Order

1. Read `UnreachableCode`
2. Read `_SENDER_BY_CODE`
3. Read `who_sends()`
4. Read `make_port_unreachable()`
5. Read `make_frag_needed()`
6. Run `examples/icmp/session_02_walkthrough.py`

## Read It Like Code

```python
who_sends(code: UnreachableCode) -> str

make_port_unreachable(quoted: QuotedPacket) -> IcmpMessage

make_frag_needed(quoted: QuotedPacket, next_hop_mtu: int) -> IcmpMessage
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `UnreachableCode.PORT_UNREACHABLE` | The one code in this table sent by the *destination*, not a router along the path. The packet arrived; nobody was listening on that port. |
| `UnreachableCode.NET_UNREACHABLE` / `HOST_UNREACHABLE` | Both come from a router that ran out of route — the packet never got close to the destination. |
| `next_hop_mtu` (in `make_frag_needed`) | Not a status flag — a number the sender is expected to read and act on. It's the entire mechanism behind Path MTU Discovery. |
| `quoted` (on every builder) | Carried through unchanged from caller to `IcmpMessage`. The builder's job is to attach the right `icmp_type`/`code`, not to touch the quote. |

## Decision Flow

```text
who reported this?
  NET_UNREACHABLE / HOST_UNREACHABLE -> a router along the path (no route left to try)
  PORT_UNREACHABLE                   -> the destination host itself (packet arrived, nobody listening)
  FRAG_NEEDED                        -> the router whose outbound link is too small for the packet
```

## Reading Lens

The important move in this session is to stop reading "Destination Unreachable" as a single failure and start asking, for any given code:

- did this packet ever reach the destination host, or did a router give up first?
- is this message reporting a routing problem, a listening problem, or a size problem?
- if this is frag-needed, what number is riding along, and who is supposed to read it?

## Toy Model Boundary

Real ICMP generation is rate-limited by the sending router or host, so a burst of unreachable packets doesn't turn into a flood back at the source — this lesson has no rate limiting at all. This module is also IPv4-only; ICMPv6 folds "too big" into its own type rather than a Destination-Unreachable code, so `make_frag_needed`'s shape doesn't carry over directly.

## Code Landmarks

### `_SENDER_BY_CODE`

A plain dict, one line per code. Read the comment above it before the dict itself — it states the sender for all four codes in prose, and the dict is just that prose made queryable.

### `who_sends()`

One line: a dict lookup. All the teaching content lives in the table it reads from, not in this function.

### `make_port_unreachable()`

Builds a `DEST_UNREACHABLE` message with `code=PORT_UNREACHABLE.value`. The docstring frames it as a confession: "I got it, nobody was home" — worth reading as the destination host's own voice, not a router's.

### `make_frag_needed()`

The `code` string embeds `next_hop_mtu` directly (`f"{...} (next-hop MTU {next_hop_mtu})"`). That's the one-sentence version of Path MTU Discovery: the sender reads this number out of the error and shrinks future packets to fit.

## Failure Questions

Use the source file to answer these:

1. Which two codes in `_SENDER_BY_CODE` are reported by "a router along the path," and what do they have in common that separates them from `PORT_UNREACHABLE`?
2. Why is port-unreachable described as a *different kind* of failure rather than just another routing failure — what has to be true about the packet's journey for this code to be sent at all?
3. What does `make_frag_needed()` do with `next_hop_mtu` that `make_port_unreachable()` doesn't do with any equivalent value?
4. If you call `make_port_unreachable(quoted)`, what `icmp_type` does the resulting `IcmpMessage` carry, and where in the source is that decided?
5. Does `who_sends()` know anything about a specific packet, or only about the code? What does that tell you about what this function can and can't answer?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/icmp/session_02_walkthrough.py
```

The walkthrough reads `who_sends()` for all four codes, then builds a frag-needed message and a port-unreachable message and checks what each one carries.

## Done When

The learner can say all of the following without looking at notes:

- "Net-unreachable and host-unreachable come from a router giving up; port-unreachable comes from the destination itself."
- "Port-unreachable means the packet arrived — that's a fundamentally different failure from a router with no route."
- "Frag-needed isn't just a rejection — the MTU it carries is the whole mechanism Path MTU Discovery runs on."

## References

- RFC 792 (Internet Control Message Protocol)
- RFC 1191 (Path MTU Discovery) — for the `next_hop_mtu` field in `make_frag_needed()`
