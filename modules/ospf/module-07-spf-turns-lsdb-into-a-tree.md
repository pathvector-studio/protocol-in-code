# Session 07: SPF Turns The LSDB Into A Tree

## Question

What are the exact inputs to SPF, and what object does SPF return?

## Source

- `src/protocol_in_code/ospf/spf.py`

## Read Order

1. Read `build_graph()`.
2. Read `SPFTree`.
3. Read `shortest_path_tree()`.

## Bridge From Previous Sessions

Sessions 04-06 built the stable LSDB object.
This session turns that object into a router-only graph and then into a shortest-path tree.

## Walkthrough

```bash
PYTHONPATH=src python3 examples/ospf/session_07_walkthrough.py
```

## Simplification Note

This is a compact Dijkstra implementation for readability.
It shows the shape of SPF, not every OSPF optimization.
This first OSPF arc intentionally omits Network-LSA and transit-network vertices.

## Done When

- You can say what `costs`, `parents`, and `order` each mean.
- You can explain why SPF needs LSDB first.
