# Session 01 / Module 01: A Connection Is a 5-Tuple

## Position

- Track: NAT
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/nat/module-01/index.html`
- Source file: `src/protocol_in_code/nat/five_tuple.py`
- Walkthrough script: `examples/nat/session_01_walkthrough.py`

## Core Question

What identifies a connection to the kernel, and what does it mean that the reply direction is just the same identity with two fields swapped?

## Outcome

By the end of this session, the learner should be able to:

- name the five fields that make up a `FiveTuple` and why all five are required
- list the checks `validate_tuple()` runs, and in what order
- explain what `reply_tuple()` computes and why it needs no lookup
- explain why `reply_tuple(reply_tuple(t)) == t` for every valid tuple

## Read Order

1. Read the module comment at the top of the file
2. Read `FiveTuple`
3. Read `TupleValidity`
4. Read `validate_tuple()`
5. Read `reply_tuple()`
6. Run `examples/nat/session_01_walkthrough.py`

## Read It Like Code

```python
FiveTuple(
    protocol,
    src_ip,
    src_port,
    dst_ip,
    dst_port,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `protocol` | `tcp` and `udp` are the only protocols this table understands. Everything else is rejected before it can become a key. |
| `src_ip` / `src_port` | The sender's half of the identity. On the private side, this is the real host; after SNAT, it is the public address. |
| `dst_ip` / `dst_port` | The receiver's half. On outbound traffic this rarely changes; DNAT is what changes it. |

## Decision Flow

```text
protocol not in ("tcp", "udp")     -> UnknownProtocol
src_port outside 1..65535          -> BadSrcPort
dst_port outside 1..65535          -> BadDstPort
otherwise                          -> Valid
```

## Reading Lens

The important move in this session is to stop thinking of "a connection" as a stateful thing the kernel remembers as a narrative, and start asking:

- what are the five values that make this key unique?
- is the reply just this same tuple viewed from the other side?
- did `reply_tuple()` look anything up, or did it only rearrange fields already in hand?

## Toy Model Boundary

Real conntrack implementations key on more than five fields in some modes (VRF, zone IDs, ICMP uses type/code instead of ports) and validate against interface and routing context this file never sees. This lesson keeps the tuple to exactly five fields and two protocols so the identity concept — and the involution property of `reply_tuple()` — stays the whole story, with nothing else competing for attention.

`validate_tuple()` returns an enum rather than raising, so every scenario in the walkthrough can inspect a value instead of catching an exception.

## Code Landmarks

### Module comment

The file opens with the thesis of the entire track: "the kernel does not track connections — it tracks keys." Every other file in this track (`rewrite.py`, `table.py`, `ports.py`, `timeout.py`) is built on `FiveTuple` being nothing more than a hashable value.

### `FiveTuple`

A frozen dataclass. Frozen matters: a `FiveTuple` is a value, not an object with a lifecycle. Two tuples with the same five fields are the same key, not two things that happen to look alike.

### `validate_tuple()`

The main reading target for the validity side. Three ordered checks, each returning immediately on failure — protocol first, then each port. The table only ever indexes on tuples worth trusting; garbage is rejected here, not downstream in `table.py`.

### `reply_tuple()`

Four lines: build a new `FiveTuple` with `src_ip`/`src_port` set from the old tuple's `dst_ip`/`dst_port`, and vice versa. Nothing else changes — `protocol` carries straight through. It is a pure, total function: it never fails, never consults a table, and calling it twice returns the original tuple, because swapping two pairs of fields twice is the identity operation.

## Failure Questions

Use the source file to answer these:

1. What validity comes back for a tuple with `protocol="icmp"`, and which check catches it first if the ports are also out of range?
2. Why does `src_port=0` fail validation while `src_port=1` passes? Which constant in the file decides the boundary?
3. What field does `reply_tuple()` leave completely unchanged, and why must it?
4. Why is `reply_tuple(reply_tuple(t)) == t` guaranteed by the field assignments alone, without needing a proof beyond reading the function?
5. If two `FiveTuple` values have every field equal, does `validate_tuple()` need to run twice to know they're the same key? What does "frozen dataclass" already guarantee here?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/nat/session_01_walkthrough.py
```

The walkthrough builds one valid tuple, breaks it three different ways to hit each `TupleValidity` outcome, then swaps it with `reply_tuple()` and swaps it again to show the involution.

## Done When

The learner can say all of the following without looking at notes:

- "A connection's identity is exactly five fields — protocol plus both endpoints — nothing more, nothing less."
- "Validation is three ordered, independent checks, and any one of them can reject the tuple before it ever reaches a table."
- "`reply_tuple()` is not a lookup; it is a pure swap, and swapping twice always returns the original tuple."

## References

- RFC 2663, Section 4 (NAT Terminology and Considerations — traditional NAT and the notion of a session/connection binding)
