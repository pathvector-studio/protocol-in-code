# Session 08: The Tree Becomes Routes

## Question

How does the shortest-path tree turn into actual reachable prefixes?

## Source

- `src/protocol_in_code/ospf/routing.py`

## Read Order

1. Read `OSPFRoute`.
2. Read `_first_hop()`.
3. Read `routes_from_tree()`.

## Walkthrough

```bash
PYTHONPATH=src python3 examples/ospf/session_08_walkthrough.py
```

## Done When

- You can explain why the route cost includes both tree cost and stub metric.
- You can explain how the next hop is recovered from `parents`.

