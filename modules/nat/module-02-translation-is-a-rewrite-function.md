# Session 02 / Module 02: Translation Is a Rewrite Function

## Position

- Track: NAT
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/nat/module-02/index.html`
- Source file: `src/protocol_in_code/nat/rewrite.py`
- Walkthrough script: `examples/nat/session_02_walkthrough.py`

## Core Question

When a router performs NAT, does it change the packet, or does it produce a new packet and let the old one go?

## Outcome

By the end of this session, the learner should be able to:

- name the one field SNAT changes and the one field DNAT changes
- explain why `apply_snat()` and `apply_dnat()` return a new `Packet` instead of modifying the argument
- explain how `apply()` decides which rewrite to run
- explain what "frozen in, frozen out" means for testing NAT logic

## Read Order

1. Read `RewriteKind`
2. Read `Packet`
3. Read `RewriteSpec`
4. Read `apply_snat()`
5. Read `apply_dnat()`
6. Read `apply()`
7. Run `examples/nat/session_02_walkthrough.py`

## Read It Like Code

```python
Packet(
    tuple,
    payload_note,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `Packet.tuple` | The `FiveTuple` from Session 01. This is what NAT actually rewrites — the packet's routing identity. |
| `Packet.payload_note` | A stand-in for everything NAT does not touch. Carried through every rewrite unchanged, on purpose. |
| `RewriteSpec.kind` | `SNAT` or `DNAT` — which half of the tuple this spec is allowed to touch. |
| `RewriteSpec.ip` / `RewriteSpec.port` | The replacement values. Where they land depends entirely on `kind`. |

## Decision Flow

```text
spec.kind is SNAT   -> apply_snat(packet, spec.ip, spec.port)  (rewrites src_ip, src_port only)
spec.kind is DNAT   -> apply_dnat(packet, spec.ip, spec.port)  (rewrites dst_ip, dst_port only)
```

## Reading Lens

The important move in this session is to stop picturing NAT as "the router edits the packet in place" and start asking:

- which two fields out of five does this rewrite touch?
- what happens to the `Packet` object I passed in — does it look any different after the call?
- if I had to log every rewrite for debugging, could I diff the input and output tuples and see exactly one pair of fields change?

## Toy Model Boundary

Real NAT implementations recompute IP and transport checksums after every rewrite (the IP header checksum and the TCP/UDP checksum both depend on address and port fields), and many also handle ICMP translation and protocol-specific quirks (FTP's embedded IP addresses, for instance). This file rewrites only the `FiveTuple` and leaves `payload_note` untouched — there is no checksum field to recompute and no ICMP branch. The lesson here is the shape of the substitution, not the full packet-mutation cost real NAT pays.

`Packet` and `FiveTuple` are both frozen dataclasses, which is what makes "return a new object" the only option — there is no `.tuple = ...` to fall back on even if you wanted one.

## Code Landmarks

### `RewriteKind`

Two values, `SNAT` and `DNAT`. This is the only branch point in the whole file — everything else is straight-line code once you know which kind you have.

### `apply_snat()`

Builds a new `FiveTuple` where `src_ip` and `src_port` come from the function's arguments and `dst_ip`/`dst_port`/`protocol` are copied straight from `packet.tuple`. Then wraps it in a new `Packet` carrying the same `payload_note`. The original `packet` argument is never assigned to.

### `apply_dnat()`

Same shape as `apply_snat()`, mirrored: `dst_ip`/`dst_port` come from the arguments, `src_ip`/`src_port`/`protocol` are copied through untouched.

### `apply()`

The dispatcher, exported at package level as `apply_rewrite`. One `if` on `spec.kind`, delegating to whichever of the two functions matches. It takes a `RewriteSpec` as data — this is what lets a rule table hand rewrites around as values instead of as code paths.

## Failure Questions

Use the source file to answer these:

1. Which two fields does `apply_snat()` write from its own arguments, and which three fields does it copy from `packet.tuple`?
2. After calling `apply_dnat(packet, "10.0.0.100", 8080)`, what is `packet.tuple.dst_ip`? Why does the *original* `packet` not reflect the new value?
3. What field of `Packet` is identical between the input and every rewritten output, no matter which kind of NAT ran?
4. If `spec.kind` is neither `SNAT` nor `DNAT`, what does `apply()` do? What does that tell you about how `RewriteKind` is meant to be used?
5. Why does `apply()` take a `RewriteSpec` instead of separate `kind`, `ip`, and `port` arguments?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/nat/session_02_walkthrough.py
```

The walkthrough runs SNAT and DNAT on the same starting packet, confirms each rewrite only touches its own two fields, confirms the original packet object is unchanged after both calls, and confirms `apply()` reaches the same results as calling `apply_snat()`/`apply_dnat()` directly.

## Done When

The learner can say all of the following without looking at notes:

- "SNAT rewrites the source address and port; DNAT rewrites the destination address and port; neither touches the other half."
- "The router never mutates a packet — it substitutes a new one and lets the old one go."
- "`apply()` is a thin dispatcher over `RewriteSpec.kind`; the real rewrite logic lives in `apply_snat()` and `apply_dnat()`."

## References

- RFC 2663, Section 4.1 (Traditional NAT: Basic NAT / NAPT — source address and port translation)
