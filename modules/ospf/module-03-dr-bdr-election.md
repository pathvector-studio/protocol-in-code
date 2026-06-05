# Session 03: DR And BDR Election

## Question

If several routers share one broadcast segment, how does the code pick DR and BDR?

## Source

- `src/protocol_in_code/ospf/dr_election.py`

## Read Order

1. Read `InterfaceCandidate`.
2. Read `_pick_highest()`.
3. Read `elect_dr_bdr()`.

## Bridge From Previous Session

Session 02 showed that some neighbors on a broadcast segment stop at `2-Way`.
This session explains the shared-segment branch that follows from that fact: DR / BDR election.

## Walkthrough

```bash
PYTHONPATH=src python3 examples/ospf/session_03_walkthrough.py
```

## Simplification Note

This is a teaching election model.
It keeps the logic readable by focusing on priority, declared role, and router ID tie-breaks, and leaves the full non-preemptive election rules for a later pass.

## Done When

- You can explain why priority `0` disappears from the candidate set.
- You can explain why router ID still matters after priority.
