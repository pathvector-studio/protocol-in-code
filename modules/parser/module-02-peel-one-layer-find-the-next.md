# Session 02 / Module 02: Peel One Layer, Find the Next

## Position

- Track: Packet Parser
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/parser/module-02/index.html`
- Source file: `src/protocol_in_code/parser/dispatch.py`
- Walkthrough script: `examples/parser/session_02_walkthrough.py`

## Core Question

Once a header has been sliced off, something has to decide what kind of bytes come next — how does a number like `0x0800` or `6` turn into a decision about which parser to call?

## Outcome

By the end of this session, the learner should be able to:

- name the two lookup tables `dispatch.py` defines and what each one's keys mean
- explain what `next_layer()` and `transport_protocol()` return for a number that isn't in their table
- explain why "unknown" is a valid, expected outcome rather than an error
- state, in one sentence, what demultiplexing actually is at the code level

## Read Order

1. Read `ETHERTYPES`
2. Read `IP_PROTOCOLS`
3. Read `LayerId`
4. Read `next_layer()`
5. Read `transport_protocol()`
6. Run `examples/parser/session_02_walkthrough.py`

## Read It Like Code

```python
ETHERTYPES: dict[int, str] = {
    0x0800: "IPv4",
    0x0806: "ARP",
    0x86DD: "IPv6",
}
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `ETHERTYPES` | Maps the 2-byte ethertype from Session 01's header to the name of the layer above it. |
| `IP_PROTOCOLS` | Maps the IP protocol number (from Session 03's header) to the name of the transport layer above it. |
| `LayerId.UNKNOWN` | The fallback for any key neither dict recognizes — not an exception, not a crash. |

## Decision Flow

```text
key in table       -> LayerId for the mapped name (dict lookup succeeds)
key not in table   -> LayerId.UNKNOWN (dict.get() fallback)
```

## Reading Lens

The important move in this session is to stop thinking of "protocol dispatch" as something clever and start asking:

- is this key actually present in the dict, or does it fall through to `.get()`'s default?
- what's the smallest possible implementation of "find the next layer" — and is that exactly what's here?
- what happens to a number this dict has never heard of?

## Toy Model Boundary

`ETHERTYPES` holds three entries and `IP_PROTOCOLS` holds three entries. The real registries — IANA's EtherType list and IANA's IP protocol number list — hold hundreds, covering everything from MPLS to SCTP to GRE. This lesson keeps both tables tiny so the lookup-plus-fallback shape stays the entire story; nothing about the shape changes when a table grows from three entries to three hundred.

## Code Landmarks

### `ETHERTYPES` / `IP_PROTOCOLS`

Two plain dict literals. The header comment calls them "the entire protocol stack as far as a dispatcher is concerned" — read that literally. There is no class hierarchy, no registry object, no plugin system. A number comes in, a name comes out.

### `next_layer()`

```python
name = ETHERTYPES.get(ethertype)
if name is None:
    return LayerId.UNKNOWN
return LayerId(name)
```

Three lines: look up, check for absence, wrap the result. This is the entire function.

### `transport_protocol()`

The same three-line shape as `next_layer()`, pointed at `IP_PROTOCOLS` instead of `ETHERTYPES`. Reading the two functions side by side is the fastest way to see that "dispatch" is one pattern applied twice, not two different mechanisms.

## Failure Questions

Use the source file to answer these:

1. What does `next_layer(0x8847)` return, and which line of `next_layer()` produces that value?
2. Why does `next_layer()` call `ETHERTYPES.get(ethertype)` instead of `ETHERTYPES[ethertype]`?
3. `LayerId` is defined once but populated from two different dicts (`ETHERTYPES` and `IP_PROTOCOLS`). What has to be true about the strings in both dicts for `LayerId(name)` to succeed?
4. If IANA assigned a new ethertype tomorrow, what line(s) in `dispatch.py` would need to change to recognize it?
5. Why is `transport_protocol()` a separate function from `next_layer()` instead of one function parameterized by which dict to use?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/parser/session_02_walkthrough.py
```

The walkthrough checks `next_layer()` against a known and an unknown ethertype, `transport_protocol()` against a known and an unknown protocol number, and closes by showing that `next_layer()` is exactly `ETHERTYPES.get(...)` with nothing hidden behind it.

## Done When

The learner can say all of the following without looking at notes:

- "Both dispatch functions are the same three lines: look up, check for None, wrap in LayerId."
- "An ethertype or protocol number this code has never seen returns UNKNOWN, not an error."
- "Demultiplexing is table lookup — teaching the dispatcher a new protocol means adding one dict entry."

## References

- RFC 894 (A Standard for the Transmission of IP Datagrams over Ethernet Networks) — the origin of the ethertype-as-dispatch-key convention this module reads from
