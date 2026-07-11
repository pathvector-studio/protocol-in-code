# Session 06 / Module 06: Build the Toy NAT Box Loop

## Position

- Track: NAT
- Session: 06
- Site lesson: `pathvector-site/courses/protocols-in-code/nat/module-06/index.html`
- Source file: `src/protocol_in_code/nat/nat_loop.py`
- Walkthrough script: `examples/nat/session_06_walkthrough.py`

## Core Question

Every earlier session in this track taught one piece — the tuple, the rewrite, the table, the port pool, the clock. What does a packet's actual round trip through all five look like when they are wired into one box?

## Outcome

By the end of this session, the learner should be able to:

- trace `outbound()`'s two branches (`FORWARD` reuse vs. new allocation) and `inbound()`'s two branches (`REVERSE` un-NAT vs. drop)
- explain why the packet `run_flow()` delivers is addressed to the private host's original source, and why that is `reply_tuple(private_tuple)` and not `private_tuple` itself
- explain "NAT as accidental firewall" — why an inbound packet with no table entry is a drop, not an error
- name which earlier session's module owns each field and function `ToyNatBox` wires together

## Read Order

1. Read `ToyNatBox`'s field list
2. Read `tick()`
3. Read `outbound()`
4. Read `inbound()` and its docstring
5. Read `run_flow()`, including its trailing comment and assertions
6. Run `examples/nat/session_06_walkthrough.py`

## Read It Like Code

```python
ToyNatBox(
    public_ip,
    table,
    allocator,
    clock,
    trace,
)
```

## Parts List

Every field and function `nat_loop.py` imports was taught by an earlier session in this track. The capstone's only new code is the wiring between them.

| Source file | Session that taught it | What it contributes to `ToyNatBox` |
|---|---|---|
| `five_tuple.py` — `FiveTuple`, `reply_tuple` | 01 | The wire identity every function below reads, rewrites, or swaps. `outbound()` builds a fresh `FiveTuple` for the translated side; `reply_tuple()` computes the far side's reply direction and the private host's reply direction. |
| `rewrite.py` — `Packet`, `apply_snat`, `apply_dnat` | 02 | `apply_snat()` runs inside `outbound()` on every new or reused flow; `apply_dnat()` runs inside `inbound()` to restore the private host's original address. Packets are never mutated, only substituted. |
| `table.py` — `ConntrackTable`, `NatEntry`, `MatchDirection`, `insert`, `match` | 03 | `self.table`; `match()` is the first call in both `outbound()` and `inbound()` and its `MatchDirection` return value (`FORWARD` / `REVERSE` / `NO_MATCH`) drives every branch in this module. |
| `ports.py` — `PortAllocator`, `allocate_port`, `AllocationOutcome` | 04 | `self.allocator`; `outbound()` calls `allocate_port()` only on the new-flow branch, and its `None` result becomes the `POOL_EXHAUSTED` drop. |
| `timeout.py` — `sweep`, `touch` | 05 | `tick()` calls `sweep()` directly; both `outbound()`'s reuse branch and `inbound()`'s un-NAT branch call `touch()` on every matched entry before re-inserting it under both keys. |

## Decision Flow

```text
tick(seconds):
  clock += seconds
  sweep(table, clock) -> for every expired entry, discard its port, trace it

outbound(packet):
  match(table, packet.tuple)
    FORWARD  -> touch(entry, clock), re-insert under both keys,
                apply_snat(packet, entry.translated.src_ip, entry.translated.src_port)
    (no match) -> allocate_port(allocator)
                    None -> trace drop (POOL_EXHAUSTED), return None
                    port -> build translated FiveTuple, NatEntry, insert(),
                             apply_snat(packet, public_ip, port)

inbound(packet):
  match(table, packet.tuple)
    REVERSE    -> touch(entry, clock), re-insert under both keys,
                  apply_dnat(packet, entry.original.src_ip, entry.original.src_port)
    NO_MATCH or FORWARD -> trace drop ("no entry, treated as unsolicited"), return None

run_flow(box, private_tuple):
  translated = box.outbound(Packet(private_tuple, "request"))
  reply = Packet(reply_tuple(translated.tuple), "response")
  delivered = box.inbound(reply)
  # delivered.tuple == reply_tuple(private_tuple), not private_tuple
```

## Reading Lens

The important move in this session is to stop reading each module in isolation and start asking, at every line of `outbound()` and `inbound()`:

- which of the five imported modules is doing the actual work on this line?
- did `match()` return `FORWARD`, `REVERSE`, or `NO_MATCH` — and does this function even distinguish all three, or collapse two of them into one branch?
- what changed in `self.trace`, and would that one line alone tell a debugger what happened to this packet?
- whose address is in `src` and whose is in `dst` on the packet this function returns — the private host's, or the public IP's?

## Toy Model Boundary

This module has no hairpinning: a private host addressing another private host behind the *same* public IP is not handled — there is no code path that recognizes an outbound packet's destination as one of the box's own translated tuples and loops it back inbound instead of sending it out. There are no Application-Level Gateways (ALGs) — protocols like FTP or SIP that embed IP addresses and ports inside their payload, which real NAT devices must rewrite in the payload itself, are entirely out of scope; this toy only ever rewrites the five-tuple. There is no ICMP handling — real NAT boxes must translate the *embedded* original tuple inside ICMP error messages (e.g., Destination Unreachable, TTL Exceeded) so the private host can identify which of its own flows failed; nothing here parses ICMP payloads. `inbound()` also does not distinguish "no entry because this is a new inbound connection attempt" from "no entry because the flow already expired" — both collapse to the same `NO_MATCH` drop and the same trace line.

## Code Landmarks

### `ToyNatBox.__post_init__`

Builds a default `PortAllocator` bound to the same `public_ip` if none is supplied — the two are meant to travel together, one pool per public address (Session 04).

### `tick()`

The only place `sweep()` is called from inside `nat_loop.py`. Advancing the clock is the only way an idle entry's port is ever returned to the pool — no packet does it.

### `outbound()`'s two branches

`FORWARD` means this exact tuple has been seen before — `touch()` and reuse. Anything else means a new flow, which is where `allocate_port()` can return `None` and the packet dies quietly, traced as `POOL_EXHAUSTED`.

### `inbound()`'s docstring

"No match here does not mean an error — it means nobody inside asked for this." A NAT table with no entry for an inbound tuple behaves exactly like a firewall that default-denies everything it did not see leave first. This is the accidental-firewall property, and it is a direct consequence of Session 03's `match()` returning `NO_MATCH` for anything the table never inserted.

### `run_flow()`'s trailing comment and assertions

The single clearest statement in this file of the distinction the whole session turns on: the delivered packet is addressed *to* the private host, so its tuple is `reply_tuple(private_tuple)` — src and dst swapped from what the private host originally sent — not `private_tuple` unchanged. The far end's address never changes; only the destination gets un-NATed back to the private host's own original source.

## Failure Questions

Use the source file to answer these:

1. `allocate_port()` scans from `next_candidate` and wraps once (Session 04). Nothing in `outbound()` retries or handles partial exhaustion specially — what exactly does `outbound()` do the instant `allocate_port()` returns `None`?
2. `sweep()` (Session 05) deletes both `entry.original` and `reply_tuple(entry.translated)` from the table. If `tick()`'s `sweep()` call only deleted one of those two keys, what would happen the next time a reply for that flow arrived at `inbound()`?
3. `run_flow()` asserts `delivered.tuple == reply_tuple(private_tuple)`, not `delivered.tuple == private_tuple`. What are the `src_ip` and `src_port` of `reply_tuple(private_tuple)`, and whose address are they — the private host's, or the far side's?
4. `touch()` (Session 05) returns a new frozen `NatEntry`; it does not mutate the entry passed in. In `outbound()`'s `FORWARD` branch, what two lines make sure the *table* actually reflects the touched entry, not the stale one `match()` returned?
5. `inbound()` treats `NO_MATCH` as a silent drop with no distinct signal back to the caller beyond `None`. What field of `ToyNatBox` is the only record that this drop ever happened, and what would a debugger have to read to find it?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/nat/session_06_walkthrough.py
```

The walkthrough builds one `ToyNatBox`, runs a full `run_flow()` for a UDP flow and checks the outbound packet is translated to the box's public IP and a port drawn from the ephemeral range, checks the delivered reply's tuple equals `reply_tuple(private_tuple)` — addressed to the private host's own original source, not equal to `private_tuple` itself — sends a second outbound packet on the same flow and confirms it reuses the same public port rather than allocating a new one, sends an inbound packet with no matching table entry and confirms it is dropped (`None`), ticks the clock past the 30-second UDP timeout and confirms the flow's conntrack entry is swept from the table, then confirms a reply arriving after that expiry finds `NO_MATCH` and is dropped silently — the hole-punched-in-reverse scenario from Session 05.

## Done When

The learner can say all of the following without looking at notes:

- "Every field and function in ToyNatBox belongs to an earlier session; outbound() and inbound() only wire them together around one match() call each."
- "The delivered packet is reply_tuple(private_tuple), not private_tuple — it's addressed to the private host, with src and dst swapped from what that host originally sent."
- "An inbound packet with no table entry is not an error. NAT with no matching state is indistinguishable from a default-deny firewall."
- "Nothing frees a port or a table entry on its own. tick() -> sweep() is the only thing that does — no packet triggers it."

## References

- RFC 2663 (IP Network Address Translator (NAT) Terminology and Considerations)
- RFC 4787 (NAT UDP Behavioral Requirements)
