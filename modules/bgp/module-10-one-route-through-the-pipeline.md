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

## Read Order

1. Read `PipelinePolicies`
2. Read `PipelineResult`
3. Read `candidate_from_attributes()`
4. Read `apply_policy_action()`
5. Read `process_single_route()`
6. Run `examples/bgp/session_10_walkthrough.py`

## Read It Like Code

```python
store_received_path(adj_rib_in, peer_id, prefix, attributes)
validation_state = validate_origin(route, vrps)
imported = apply_import_policy(raw_candidate, validation_state, policies.import_policy)
action = decide_route_policy(validation_state, policies.validation_policy)
installed = apply_policy_action(imported, action)
install_best_path(loc_rib, installed)
exported = prepare_export(installed, export_peer_type, policies.export_policy)
```

## Data That Matters

| Item | Why it matters |
|---|---|
| `PipelinePolicies` | Keeps import, validation, and export concerns separate. |
| `PipelineResult` | Makes the final state explicit. |
| `origin_as_from_attributes()` | Bridges Session 02 attributes into Session 04 validation input. |
| `apply_policy_action()` | Turns abstract policy output into a concrete candidate or drop. |

## Failure Questions

1. Which step happens before validation?
2. Which step can drop the route before installation?
3. Which step lowers local preference without rejecting the route?
4. Which step changes the outbound AS path?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/bgp/session_10_walkthrough.py
```

The walkthrough takes one valid route through import policy, validation, policy action, Loc-RIB installation, and eBGP export.

## Done When

The learner can say all of the following without looking at notes:

- "One route moves through a predictable chain of functions."
- "Validation result and policy action are still separate, even in the full pipeline."
- "Loc-RIB and Adj-RIB-Out change at different points."
- "The course now reads like one small control plane instead of disconnected examples."
