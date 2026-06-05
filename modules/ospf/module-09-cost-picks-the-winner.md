# Session 09: Cost Picks The Winner

## Question

If the same prefix appears more than once, which route wins?

## Source

- `src/protocol_in_code/ospf/cost.py`

## Read Order

1. Read `RouteDecision`.
2. Read `select_best_route()`.
3. Read `select_best_routes()`.

## Bridge From Previous Session

Session 08 built route candidates.
This session shows the final route-type-first, then cost-based choice when candidates overlap.

## Walkthrough

```bash
PYTHONPATH=src python3 examples/ospf/session_09_walkthrough.py
```

## Simplification Note

The tie-breaks here are kept intentionally small so the first comparison stays visible.
This model prefers intra-area over inter-area before comparing total cost, and it does not model ECMP.

## Done When

- You can name the first field that decides the winner.
- You can explain what happens when two candidates have the same total cost.
