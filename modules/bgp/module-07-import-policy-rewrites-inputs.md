# Session 07 / Module 07: Import Policy Rewrites Inputs

## Position

- Track: BGP
- Session: 07
- Site lesson: `pathvector-site/courses/protocols-in-code/bgp/module-07/index.html`
- Source file: `src/protocol_in_code/bgp/import_policy.py`
- Walkthrough script: `examples/bgp/session_07_walkthrough.py`

## Core Question

How does local import policy change or reject a path before best-path selection runs?

## Outcome

By the end of this session, the learner should be able to:

- explain why import policy sits before best-path selection
- explain how local policy can rewrite `local_pref` or `weight`
- explain how local policy can drop a path before comparison
- explain why the same route can look different after import policy

## Bridge From Previous Sessions

Session 05 separated validation result from action. Session 07 adds another layer: even before final best-path selection, local import policy can rewrite or reject a candidate.

## Read Order

1. Read `ImportPolicy`
2. Read `apply_import_policy()`
3. Notice the early returns
4. Notice the `replace()` calls
5. Run `examples/bgp/session_07_walkthrough.py`

## Read It Like Code

```python
if candidate.next_hop in policy.reject_next_hops:
    return None

if validation_state is ValidationState.INVALID and policy.reject_invalid:
    return None

updated = replace(updated, local_pref=policy.local_pref_override)
updated = replace(updated, weight=policy.weight)
```

## Data That Matters

| Item | Why it matters |
|---|---|
| `local_pref_override` | Rewrites an input to Session 03. |
| `weight` | Adds vendor-local preference before comparison. |
| `reject_next_hops` | Drops a path before it reaches best-path selection. |
| `reject_invalid` | Lets validation state influence import behavior. |

## Failure Questions

1. Which conditions return `None`?
2. What happens if only `local_pref_override` is set?
3. What happens if only `weight` is set?
4. Why is rewriting inputs different from final rejection?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/bgp/session_07_walkthrough.py
```

The walkthrough shows one path being rewritten, one path getting a local weight, one path being dropped by next-hop rule, and one invalid path being rejected before best-path.

## Done When

The learner can say all of the following without looking at notes:

- "Import policy runs before best-path."
- "Import policy can rewrite `local_pref` and `weight`."
- "Import policy can drop a path before comparison."
- "The candidate entering best-path is not always the one the peer originally sent."
