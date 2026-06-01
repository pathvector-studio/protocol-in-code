# Session 05 / Module 05: Validation State Does Not Act By Itself

## Position

- Track: BGP
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/bgp/module-05/index.html`
- Source file: `src/protocol_in_code/bgp/policy.py`
- Walkthrough script: `examples/bgp/session_05_walkthrough.py`

## Core Question

What happens after origin validation returns `valid`, `invalid`, or `not_found`, and why does the result still need routing policy?

## Outcome

By the end of this session, the learner should be able to:

- explain why validation state is an input to policy, not an action by itself
- explain why an `invalid` route does not automatically disappear
- explain how one policy can reject `invalid` while another merely deprioritizes it
- explain why `not_found` may still be accepted depending on policy

## Read Order

1. Read `PolicyAction`
2. Read `ValidationPolicy`
3. Read `decide_route_policy()`
4. Run `examples/bgp/session_05_walkthrough.py`
5. Explain why each validation state produced each policy action

## Read It Like Code

```python
if validation_state is ValidationState.INVALID:
    if policy.reject_invalid:
        return PolicyAction.REJECT
    return PolicyAction.DEPRIORITIZE

if validation_state is ValidationState.NOT_FOUND and policy.deprioritize_not_found:
    return PolicyAction.DEPRIORITIZE

return PolicyAction.ACCEPT
```

## Data That Matters

| Item | Why it matters |
|---|---|
| `validation_state` | This is the result from Session 04. |
| `reject_invalid` | Controls whether invalid routes are dropped or kept with lower preference. |
| `deprioritize_not_found` | Controls whether not-found routes are still accepted normally or treated with caution. |
| `PolicyAction` | Makes the policy outcome explicit: accept, deprioritize, or reject. |

## Reading Lens

The important move in this session is to stop saying "RPKI invalid means the router rejects it" and start asking:

- what validation state came back?
- what local policy is configured?
- what concrete action follows from that policy?

## Code Landmarks

### `PolicyAction`

This tells you which actions the local policy can take.

### `ValidationPolicy`

This tells you which knobs exist in the simplified model.

### `decide_route_policy()`

This is the main reading target for Session 05.

It answers:

- when `invalid` becomes `reject`
- when `invalid` only becomes `deprioritize`
- when `not_found` is still accepted

## Failure Questions

Use the source file to answer these:

1. What happens to `invalid` when `reject_invalid` is `False`?
2. What happens to `invalid` when `reject_invalid` is `True`?
3. What happens to `not_found` when `deprioritize_not_found` is `False`?
4. What happens to `not_found` when `deprioritize_not_found` is `True`?
5. Why is policy still separate from validation?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/bgp/session_05_walkthrough.py
```

The walkthrough prints several combinations of validation result and local policy, and shows the resulting policy action.

## Done When

The learner can say all of the following without looking at notes:

- "`invalid` is a validation result, not an automatic drop."
- "A router can reject invalid routes or just deprioritize them, depending on policy."
- "`not_found` can still be accepted."
- "Validation and policy are separate layers."

## References

- RFC 6811 Section 2.1
- RFC 6811 Section 3
