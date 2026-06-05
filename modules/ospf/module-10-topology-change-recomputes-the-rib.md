# Session 10: Topology Change Recomputes The RIB

## Question

When a Router-LSA changes, which part of the route table has to be recomputed?

## Source

- `src/protocol_in_code/ospf/recompute.py`

## Read Order

1. Read `recompute_area_routes()`.
2. Read `_route_index()`.
3. Read `apply_router_lsa()`.

## Bridge From Previous Sessions

Sessions 07-09 gave us SPF, routes, and final cost choice.
This session wraps them into one recompute step triggered by a changed LSA.

## Walkthrough

```bash
PYTHONPATH=src python3 examples/ospf/session_10_walkthrough.py
```

The walkthrough changes only the remote stub metric while keeping the same link set, so the route diff is attributable to one factor.

## Done When

- You can explain why a single LSA change can affect several prefixes.
- You can explain what `changed_prefixes` represents.
