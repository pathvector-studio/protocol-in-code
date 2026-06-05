# Session 02: Neighbor State Machine

## Question

How does a received Hello turn into `Init`, `2-Way`, or `Full`?

## Source

- `src/protocol_in_code/ospf/neighbor.py`

## Read Order

1. Read `NeighborState`.
2. Read `AdjacencyInputs`.
3. Read `advance_neighbor_state()`.

## Bridge From Previous Session

Session 01 told us whether a Hello is acceptable and whether the peer already sees us.
This session first turns those booleans into `Init` / `2-Way` / `ExStart`, then uses database-exchange inputs to reach `Loading` / `Full`.

## Walkthrough

```bash
PYTHONPATH=src python3 examples/ospf/session_02_walkthrough.py
```

## Simplification Note

The real state machine has more event detail.
Here the point is to separate the Hello phase from the database-exchange phase so `Full` does not look like a direct Hello outcome.

## Done When

- You can explain why some neighbors stop at `2-Way`.
- You can explain what still blocks `Full` after `ExStart`.
