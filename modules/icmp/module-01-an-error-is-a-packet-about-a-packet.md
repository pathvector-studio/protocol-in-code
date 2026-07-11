# Session 01 / Module 01: An Error Is a Packet About a Packet

## Position

- Track: ICMP
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/icmp/module-01/index.html`
- Source file: `src/protocol_in_code/icmp/message.py`
- Walkthrough script: `examples/icmp/session_01_walkthrough.py`

## Core Question

An ICMP error has to tell the original sender what went wrong — but the sender doesn't hand ICMP any context. Where does the diagnosis come from?

## Outcome

By the end of this session, the learner should be able to:

- explain why an ICMP error message contains a copy of the packet that triggered it
- state exactly how much of the original packet is quoted, and why that amount was chosen
- name the two fields inside the quote that make the error traceable to a socket
- explain why echo messages must never carry a quote

## Read Order

1. Read `IcmpType`
2. Read `ERROR_TYPES`
3. Read `QuotedPacket`
4. Read `IcmpMessage`
5. Read `validate_message()`
6. Run `examples/icmp/session_01_walkthrough.py`

## Read It Like Code

```python
QuotedPacket(
    src_ip,
    dst_ip,
    protocol,
    src_port,
    dst_port,
)

IcmpMessage(
    icmp_type,
    code,
    quoted,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `src_port` / `dst_port` | The two fields that let the original sender map this error back to the socket that caused it. Nothing else in the quote does that job. |
| `protocol` | TCP and UDP put ports in the same place in the first 8 bytes; the quote only means what it means once you know which protocol you're looking at. |
| `icmp_type` | Splits into two families — echo (payload the sender invented) and error (diagnosis) — and that split is exactly what `ERROR_TYPES` encodes. |
| `quoted` | `None` for echoes, required for errors. Its presence or absence is the entire contract `validate_message()` checks. |

## Decision Flow

```text
icmp_type in ERROR_TYPES   -> quoted MUST be present   (valid only if has_quote)
icmp_type not in ERROR_TYPES -> quoted MUST be absent   (valid only if NOT has_quote)
```

## Reading Lens

The important move in this session is to stop thinking of an ICMP error as a standalone status code and start asking:

- what packet is this error *about* — and how do I know, without a connection table?
- which two fields in the quote are the ones a real sender would actually use?
- does this message's `quoted` field match what its `icmp_type` demands?

## Toy Model Boundary

Real ICMP messages are wire bytes with a checksum and a fixed byte layout — the parser track (`src/protocol_in_code/parser/checksum.py`) owns that arithmetic. This lesson keeps the quote as a plain dataclass with named fields instead of a byte slice, so the only thing under study is *what gets quoted and why*, not how it's packed.

This module is IPv4-only. ICMPv6 (RFC 4443) reuses the same "quote the original packet" idea but with different type/code numbers and a different minimum quote size.

## Code Landmarks

### `ERROR_TYPES`

A `frozenset` of exactly two members. Everything `validate_message()` decides comes down to one membership test against this set.

### `QuotedPacket`

Frozen and five fields wide. The docstring on this class is the whole lesson: the RFC 792 quote is "the IP header plus the first 8 bytes of payload," and for TCP/UDP those first 8 bytes are the ports. Eight bytes isn't arbitrary — it's the minimum that still identifies a socket.

### `validate_message()`

Four lines. `has_quote` is computed once, then checked against `icmp_type in ERROR_TYPES` in one direction and its negation in the other. There's no third case.

## Failure Questions

Use the source file to answer these:

1. Why does RFC 792 quote exactly the first 8 bytes of the original payload — what's special about that number for TCP and UDP?
2. Which two `IcmpType` members are in `ERROR_TYPES`, and what do they have in common that the other two don't?
3. If you construct an `IcmpMessage` with `icmp_type=IcmpType.ECHO_REQUEST` and a non-`None` `quoted`, what does `validate_message()` return, and which line decides it?
4. What does `QuotedPacket.protocol` tell you that `src_port` and `dst_port` alone cannot?
5. Why is `QuotedPacket` frozen — what would change about this lesson if a quote could be mutated after the error was built?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/icmp/session_01_walkthrough.py
```

The walkthrough builds a quote once, then checks it against all four combinations of error/echo and with/without quote, before reading the ports straight off the quote.

## Done When

The learner can say all of the following without looking at notes:

- "An ICMP error is a packet about a packet — the quote is how the sender figures out what broke."
- "Eight bytes of quoted payload is exactly enough to read the ports, which is exactly enough to find the socket."
- "Errors require a quote, echoes forbid one — `validate_message()` is one membership test in two directions."

## References

- RFC 792 (Internet Control Message Protocol)
