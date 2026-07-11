# Session 01 / Module 01: Bytes Have a Shape

## Position

- Track: Packet Parser
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/parser/module-01/index.html`
- Source file: `src/protocol_in_code/parser/ethernet.py`
- Walkthrough script: `examples/parser/session_01_walkthrough.py`

## Core Question

A frame arriving off the wire is just a run of bytes — how does the parser know which bytes are the destination address, which are the source, and which name the layer above, without reading anything but position?

## Outcome

By the end of this session, the learner should be able to:

- name the byte offset where each Ethernet header field starts
- explain why the header length is fixed at 14 bytes with no length field of its own
- explain what `parse_ethernet()` returns when the frame is too short to hold a header
- describe where the payload for the next layer begins and why

## Read Order

1. Read the offset constants (`DST_OFFSET`, `SRC_OFFSET`, `TYPE_OFFSET`, `HEADER_LEN`, `MAC_LEN`)
2. Read `EthernetHeader`
3. Read `EthernetParse`
4. Read `format_mac()`
5. Read `parse_ethernet()`
6. Run `examples/parser/session_01_walkthrough.py`

## Read It Like Code

```python
EthernetHeader(
    dst_mac,
    src_mac,
    ethertype,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `dst_mac` | Bytes 0-5. Who this frame is addressed to at the link layer. |
| `src_mac` | Bytes 6-11. Who sent it, at the link layer. |
| `ethertype` | Bytes 12-13. A number that names the protocol carried in the payload — the hook the next session's dispatcher reads. |

## Decision Flow

```text
len(frame) < HEADER_LEN   -> TooShort (no header, no payload)
len(frame) >= HEADER_LEN  -> Ok (header sliced out, payload is frame[14:])
```

## Reading Lens

The important move in this session is to stop thinking of parsing as "decoding" and start asking:

- what byte offset does this field start at, and how many bytes does it occupy?
- is that offset a constant, or does it depend on something earlier in the frame?
- where does the header end and the next layer's bytes begin?

## Toy Model Boundary

Real Ethernet framing includes an optional 802.1Q VLAN tag (which shifts every offset after it by 4 bytes) and a trailing 4-byte Frame Check Sequence that this module never sees, since it typically never reaches user-space parsing code. This lesson assumes an untagged frame with exactly one fixed 14-byte header, so the three offset constants can be read as the entire truth rather than the common case.

## Code Landmarks

### `DST_OFFSET`, `SRC_OFFSET`, `TYPE_OFFSET`, `HEADER_LEN`

The comment above them says it plainly: these offsets *are* the Ethernet header. There is no other definition to consult — the numbers 0, 6, 12, 14 are the spec, restated as code.

### `format_mac()`

Six raw bytes become `"aa:bb:cc:dd:ee:ff"` by formatting each byte as two lowercase hex digits and joining with colons. Nothing here decodes meaning — a MAC address has no structure beyond "six bytes," so formatting is the only transformation available.

### `parse_ethernet()`

The whole function is one length check, three slices, and one arithmetic conversion (`int.from_bytes` for the ethertype). The length check runs first because every offset after it assumes the header actually fits — read this function to see why a header is checked as a whole before any field inside it is trusted.

## Failure Questions

Use the source file to answer these:

1. What is stored at byte offset 6, and how many bytes does it occupy?
2. Why does `parse_ethernet()` check `len(frame) < HEADER_LEN` before touching any offset, instead of catching an exception mid-slice?
3. Why is `ethertype` decoded with `int.from_bytes(..., byteorder="big")` instead of a slice like the MAC fields?
4. If `frame` is exactly 14 bytes long, what does `parsed.payload` equal, and why?
5. `format_mac()` takes a `bytes` slice and returns a `str`. What determines how many bytes that slice must contain for the output to be six colon-separated pairs?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/parser/session_01_walkthrough.py
```

The walkthrough builds a 14-byte frame from three literal pieces (dst, src, ethertype) plus a payload, parses it, then shrinks it by one byte to show the TooShort branch, and finally checks `format_mac()` in isolation.

## Done When

The learner can say all of the following without looking at notes:

- "The Ethernet header has no length field because it doesn't need one — it's always 14 bytes."
- "Every field is defined by an offset and a width, not by a delimiter or a marker."
- "The payload for the next layer is just `frame[14:]` — parsing one layer is slicing, not consuming."

## References

- IEEE 802.3 (Ethernet framing, general)
- RFC 894 (A Standard for the Transmission of IP Datagrams over Ethernet Networks)
