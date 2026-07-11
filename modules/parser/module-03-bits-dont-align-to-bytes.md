# Session 03 / Module 03: Bits Don't Align to Bytes

## Position

- Track: Packet Parser
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/parser/module-03/index.html`
- Source file: `src/protocol_in_code/parser/ip.py`
- Walkthrough script: `examples/parser/session_03_walkthrough.py`

## Core Question

Ethernet fields sit on clean byte boundaries — IPv4 doesn't. A version number and a header length share one byte, and three flag bits share a half-word with a 13-bit fragment offset. How does the parser pull an exact field out of the middle of a byte?

## Outcome

By the end of this session, the learner should be able to:

- explain why `version` and `ihl` come from one byte using `>> 4` and `& 0x0F`
- convert an IHL nibble into a header length in bytes, and explain the unit IHL actually counts
- name the three fields packed into the flags/fragment-offset half-word and the mask or bit that isolates each one
- explain the difference between `NOT_IPV4` and `BAD_IHL` as outcomes

## Read Order

1. Read the offset constants and the three bit constants (`DF_BIT`, `MF_BIT`, `FRAGMENT_OFFSET_MASK`)
2. Read `Ipv4Header`
3. Read `Ipv4Parse` and `Ipv4Outcome`
4. Read `format_ipv4()`
5. Read `parse_ipv4()`
6. Run `examples/parser/session_03_walkthrough.py`

## Read It Like Code

```python
Ipv4Header(
    version,
    ihl,
    total_length,
    identification,
    dont_fragment,
    more_fragments,
    fragment_offset,
    ttl,
    protocol,
    checksum_field,
    src,
    dst,
    header_len_bytes,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `version` | Top nibble of byte 0. Must be 4, or this isn't an IPv4 packet at all. |
| `ihl` | Bottom nibble of byte 0. Header length in 4-byte words, not bytes — the value that must be multiplied before it means anything. |
| `dont_fragment` / `more_fragments` / `fragment_offset` | Three separate values extracted from one 16-bit field at offset 6, each by a different bit operation. |
| `header_len_bytes` | `ihl * 4`. The number actually used to slice the payload — everything downstream trusts this, not `ihl` directly. |

## Decision Flow

```text
len(packet) < MIN_HEADER_LEN        -> TooShort
version != 4                        -> NotIpv4
ihl < 5 or ihl*4 > len(packet)      -> BadIhl
otherwise                           -> Ok (header parsed, payload = packet[header_len_bytes:])
```

## Reading Lens

The important move in this session is to stop reading each field as "a value" and start asking:

- which byte (or half-word) does this field share with another field?
- is this field pulled out with a shift, a mask, or both — and in what order?
- what unit does this number count in, and has it been converted to bytes yet?

## Toy Model Boundary

This parser acknowledges that `ihl > 5` means options are present — it trusts `header_len_bytes` for the payload slice — but it never parses a single option. Real IPv4 option parsing (timestamp, route record, security) is a TLV walk of its own. Fragment reassembly is also out of scope entirely: `more_fragments` and `fragment_offset` are read and exposed as fields, but nothing here collects fragments back into a whole datagram. This lesson stops at "read the field correctly," not "act on what the field means for reassembly."

## Code Landmarks

### `version_ihl >> 4` and `version_ihl & 0x0F`

One byte, two fields. The shift discards the bottom nibble to read the top one; the mask discards the top nibble to read the bottom one. Same source byte, two different operations, because the two fields don't align to different bytes — they align to different halves of one byte.

### `header_len_bytes = ihl * 4`

The comment in the source is explicit: "IHL counts 32-bit words, not bytes." Every downstream use of the header length — the `BAD_IHL` bounds check, the payload slice — uses `header_len_bytes`, never the raw `ihl` nibble. Confusing the two would silently slice the payload four times too early.

### `DF_BIT` / `MF_BIT` / `FRAGMENT_OFFSET_MASK`

```python
dont_fragment = bool(flags_fragment & DF_BIT)
more_fragments = bool(flags_fragment & MF_BIT)
fragment_offset = flags_fragment & FRAGMENT_OFFSET_MASK
```
One 16-bit value, three extractions. `DF_BIT` and `MF_BIT` isolate single bits (0x4000 and 0x2000); `FRAGMENT_OFFSET_MASK` isolates the low 13 bits (0x1FFF) that remain. The three masks partition all 16 bits between them (1 reserved bit, DF, MF, and 13 offset bits) — read them together to see that no bit is claimed twice.

### `parse_ipv4()`'s ordering of checks

Length is checked before version; version is checked before IHL bounds. Each check assumes everything before it already passed — read the function top to bottom to see why `NOT_IPV4` is returned before `ihl` is ever validated.

## Failure Questions

Use the source file to answer these:

1. Byte 0 contains `0x45`. What are `version` and `ihl` after the shift and mask, and what is `header_len_bytes`?
2. Why does `ihl` get multiplied by 4 before it's used as a slice boundary?
3. `DF_BIT = 0x4000` and `MF_BIT = 0x2000`. If `flags_fragment = 0x6000`, what are `dont_fragment` and `more_fragments`, and which bit of which byte does each come from?
4. What distinguishes a `NOT_IPV4` outcome from a `BAD_IHL` outcome — which field is checked first, and why does that order matter?
5. Why is `FRAGMENT_OFFSET_MASK` defined as `0x1FFF` rather than `0xFFFF`?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/parser/session_03_walkthrough.py
```

The walkthrough builds header bytes by hand for two version/IHL combinations (0x45 and 0x46), sets the DF bit alone in the flags/fragment-offset half-word, forces the version nibble to 6 and the IHL nibble to 4 to hit the two rejection branches, and checks that `src`/`dst` render as dotted quads.

## Done When

The learner can say all of the following without looking at notes:

- "Version and IHL are two 4-bit fields sharing one byte — a shift reads one half, a mask reads the other."
- "IHL counts 4-byte words; `header_len_bytes = ihl * 4` is the conversion that makes it usable as a slice boundary."
- "DF, MF, and the fragment offset are three fields carved out of one 16-bit value by three different bitwise operations."

## References

- RFC 791 (Internet Protocol) — the IPv4 header format this module reads field-by-field
