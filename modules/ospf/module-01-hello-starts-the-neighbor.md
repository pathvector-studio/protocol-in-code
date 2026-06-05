# Session 01: Hello Starts The Neighbor

## Question

What has to match before an OSPF Hello can even start a neighbor relationship?

## Source

- `src/protocol_in_code/ospf/hello.py`

## Read Order

1. Read `InterfaceHelloConfig`.
2. Read `OSPFHelloPacket`.
3. Read `evaluate_hello()` from top to bottom.

## Code Lens

```python
if packet.area_id != config.area_id:
    reasons.append("area_mismatch")
```

The first gate is not SPF or LSAs. It is "can this packet belong on this link at all?"
This session ends at `accepted` and `saw_self`; it does not own the adjacency state machine yet.

## Walkthrough

```bash
PYTHONPATH=src python3 examples/ospf/session_01_walkthrough.py
```

Look for one accepted Hello and one rejected Hello.

## Simplification Note

This model checks only the fields that make the first teaching gate legible.
It does not parse packets or model timers.

## Done When

- You can name the fields that must match before adjacency can continue.
- You can explain why seeing your own router ID in the neighbor list changes the next input to the adjacency state machine.
