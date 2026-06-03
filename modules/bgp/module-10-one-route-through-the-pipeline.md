# Session 10 / Module 10: One Route Through The Whole Pipeline

## Position

- Track: BGP
- Session: 10
- Site lesson: `pathvector-site/courses/protocols-in-code/bgp/module-10/index.html`
- Source file: `src/protocol_in_code/bgp/pipeline.py`
- Walkthrough script: `examples/bgp/session_10_walkthrough.py`

## Core Question

If you trace one received route end to end, which functions touch it before it becomes an advertisement or disappears?

## Outcome

By the end of this session, the learner should be able to:

- explain the whole route pipeline as a function chain
- explain how validation, import policy, policy action, installation, and export connect
- explain which objects are stored in Adj-RIB-In, Loc-RIB, and Adj-RIB-Out
- explain why "toy BGP speaker" is now a connected set of functions instead of isolated snippets

## Bridge From Previous Sessions

Sessions 01-09 introduced the pieces separately. Session 10 is the integration lesson that threads one route through those pieces without changing the reading style.

## Design Choice

This lesson uses a toy integration order on purpose.

The course first separated `best-path`, `validation`, and `policy` so each concept could be learned alone. Here they are reconnected into one small pipeline, and validation is allowed to influence import/policy before final local installation. Real implementations vary in exactly where these boundaries sit.

## Read Order

1. Read `PipelinePolicies`
2. Read `PipelineResult`
3. Read `evaluate_candidate()`
4. Read `apply_policy_action()`
5. Read `process_single_route()`
6. Run `examples/bgp/session_10_walkthrough.py`

## Read It Like Code

```python
store_received_path(adj_rib_in, peer_id, prefix, attributes)
for _, received_attributes in received_attributes_for_prefix(adj_rib_in, prefix):
    validation_state, action, installable = evaluate_candidate(prefix, received_attributes, vrps, policies)
best = select_best_path(installable_candidates)
install_best_path(loc_rib, best)
exported = prepare_export(best, export_peer_type, policies.export_policy)
```

## Data That Matters

| Item | Why it matters |
|---|---|
| `PipelinePolicies` | Keeps import, validation, and export concerns separate. |
| `PipelineResult` | Separates received-route evaluation from selected-route outcome. |
| `origin_as_from_attributes()` | Bridges Session 02 attributes into Session 04 validation input. |
| `evaluate_candidate()` | Shows how one received path becomes one installable candidate or gets dropped. |
| `candidate_count` | Shows that the integration can compare multiple surviving candidates, not just one happy-path route. |

## Failure Questions

1. Which step stores the raw received path before any selection happens?
2. Which step can drop a candidate before best-path?
3. Which step lowers local preference without rejecting the route?
4. Which step finally compares multiple surviving candidates?
5. Which step changes the outbound AS path?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/bgp/session_10_walkthrough.py
```

The walkthrough seeds one existing candidate first, then introduces a second valid route and recomputes the prefix through import policy, validation, policy action, best-path, Loc-RIB installation, and eBGP export.
The printed result now distinguishes the received route's validation/action from the selected route that wins for the whole prefix.

## Done When

The learner can say all of the following without looking at notes:

- "One route moves through a predictable chain of functions."
- "The final installed path comes from comparing all surviving candidates for that prefix."
- "Validation result and policy action are still separate, even in the full pipeline."
- "Loc-RIB and Adj-RIB-Out change at different points."
- "The course now reads like one small control plane instead of disconnected examples."
- "If no installable candidate survives, the pipeline withdraws stale installed and exported state."

## Integration Caveat

This is still a toy pipeline, not a complete BGP speaker loop.

It now recomputes best-path across multiple surviving candidates for one prefix and withdraws stale state when nothing survives, but it does not yet model peer/session gating, event dispatch, or export refresh after every recompute event.

It also derives `origin AS` from the rightmost AS in `AS_PATH`, which is only a teaching shortcut for this course, not a complete account of every real BGP origin case.
