# Session 05: Flooding Decides Where The LSA Goes

## Question

Once a newer LSA is received, where should it be forwarded next?

## Source

- `src/protocol_in_code/ospf/flooding.py`

## Read Order

1. Read `InterfaceState`.
2. Read `FloodInterface`.
3. Read `flood_lsa()`.

## Bridge From Previous Session

Session 04 gave us the object.
This session decides whether that object is new enough to keep moving.

## Walkthrough

```bash
PYTHONPATH=src python3 examples/ospf/session_05_walkthrough.py
```

## Simplification Note

This is not a full retransmission engine.
It is a readable "newer or not, and to which interfaces?" model.

## Done When

- You can explain why the incoming interface is excluded.
- You can explain why some interfaces are still not flood targets.

