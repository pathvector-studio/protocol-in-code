# Session 14: One Prefix Becomes A Decision Set

## Question

How do multiple received paths for one prefix become a policy-aware set of installable candidates?

## Source

- `src/protocol_in_code/bgp/decision_process.py`
- Companion source: `src/protocol_in_code/bgp/pipeline.py`

## Read Order

1. Read `CandidateDecision` and notice that it keeps `validation_state`, `action`, and `installed_candidate` together.
2. Read `evaluate_prefix_candidates()` and see that it loops over every peer that currently has the prefix.
3. Read `select_best_installable_for_prefix()` and confirm that best-path runs only after validation and policy filtering.

## Bridge From Previous Sessions

- Session 03 taught pure best-path selection.
- Session 04 and Session 05 split validation result from policy action.
- Session 10 integrated those pieces for one incoming route.
- This session does the same work prefix-wide across many neighbors.

## Code Lens

```python
for peer_id, attributes in received_attributes_for_prefix(adj_rib_in, prefix):
    validation_state, action, installed = evaluate_candidate(prefix, attributes, vrps, policies)
```

The important thing here is that one prefix is no longer one route.
It is a list of peer-specific possibilities.

This is also where the course restores information that `PathCandidate` intentionally dropped.
Pure best-path comparison did not need `peer_id`, but policy-aware decision making does.

## Walkthrough

Run:

```bash
PYTHONPATH=src python3 examples/bgp/session_14_walkthrough.py
```

Look for:

- one peer whose route is deprioritized by policy
- one peer whose route stays installable without change
- the final best path being chosen after that rewrite

## Done When

- You can explain why `best-path` alone is not enough once validation and policy exist.
- You can point to the loop that turns one prefix into a decision set.
