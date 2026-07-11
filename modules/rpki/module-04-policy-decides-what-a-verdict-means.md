# Session 04 / Module 04: Policy Decides What a Verdict Means

## Position

- Track: RPKI
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/rpki/module-04/index.html`
- Source file: `src/protocol_in_code/rpki/policy.py`
- Walkthrough script: `examples/rpki/session_04_walkthrough.py`

## Core Question

A verdict of VALID, INVALID, or NOT_FOUND is a fact about the world. What does a router actually do with that fact, and who decides?

## Outcome

By the end of this session, the learner should be able to:

- explain why a verdict is an input to policy, not an action by itself
- name the two booleans that span the operator spectrum from permissive to strict
- explain why INVALID does not automatically mean the route disappears
- explain why NOT_FOUND is so often accepted, and why rejecting it wholesale would be dangerous
- explain why `ACCEPT_LOWER_PREF` is named the way it is, instead of borrowing BGP's `DEPRIORITIZE`

## Read Order

1. Read the module docstring at the top of `policy.py`
2. Read `PolicyAction`
3. Read `RoutingPolicy`
4. Read `PolicyDecision`
5. Read `apply_policy()`
6. Run `examples/rpki/session_04_walkthrough.py`

## Read It Like Code

```python
if verdict is OriginVerdict.VALID:
    return PolicyDecision(PolicyAction.ACCEPT, ...)

if verdict is OriginVerdict.INVALID:
    if policy.reject_invalid:
        return PolicyDecision(PolicyAction.REJECT, ...)
    return PolicyDecision(PolicyAction.ACCEPT_LOWER_PREF, ...)

if policy.lower_pref_not_found:
    return PolicyDecision(PolicyAction.ACCEPT_LOWER_PREF, ...)
return PolicyDecision(PolicyAction.ACCEPT, ...)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `verdict` | The fact from Session 03 (`validate_origin()`): VALID, INVALID, or NOT_FOUND. Policy never changes this, only reacts to it. |
| `RoutingPolicy.reject_invalid` | The strict/permissive knob for INVALID: drop outright, or keep at lower preference. |
| `RoutingPolicy.lower_pref_not_found` | The knob for NOT_FOUND: accept at full preference, or accept but rank beneath VALID. |
| `PolicyDecision.action` | The concrete outcome: `ACCEPT`, `ACCEPT_LOWER_PREF`, or `REJECT`. |
| `PolicyDecision.note` | A human-readable reason, worth reading in the walkthrough output — it states the operational rationale, not just the branch taken. |

## Decision Flow

```text
verdict == VALID                                -> ACCEPT               (always, regardless of policy)
verdict == INVALID   and reject_invalid          -> REJECT
verdict == INVALID   and not reject_invalid      -> ACCEPT_LOWER_PREF
verdict == NOT_FOUND and lower_pref_not_found    -> ACCEPT_LOWER_PREF
verdict == NOT_FOUND and not lower_pref_not_found -> ACCEPT
```

## Reading Lens

Session 05 of the BGP track (`bgp/module-05-policy-after-validation.md`) taught this exact shape first: a validation tri-state feeding a small policy struct with two knobs, producing an action that is still separate from the fact that produced it. `rpki/policy.py`'s docstring says so directly — it mirrors `bgp/policy.py`'s `PolicyAction` / `ValidationPolicy` / `decide_route_policy()` shape.

The one deliberate difference is the naming of the demoted-accept action. BGP session 05 called it `DEPRIORITIZE`. This module calls the same idea `ACCEPT_LOWER_PREF`. Read that as a lesson in itself: the RPKI version spells out, in the name, that the route is still an *accept* — it stays in the RIB, it just loses tiebreaks. `DEPRIORITIZE` alone does not tell you whether the route is even reachable anymore; `ACCEPT_LOWER_PREF` cannot be misread that way. When you read `apply_policy()`, ask at each branch:

- is this verdict a fact, or is `apply_policy()` about to turn it into an action?
- which of the two booleans, if any, is doing the deciding on this line?
- does the resulting action ever imply the route left the RIB, or only that it lost preference?

## Toy Model Boundary

Real routers configure RPKI policy with much richer knobs than two booleans — per-neighbor overrides, local-preference adjustments by exact amount, community tagging for downstream policy, and sometimes different stances per address family or per peer type (customer vs. peer vs. transit). `RoutingPolicy` collapses all of that to `reject_invalid` and `lower_pref_not_found` because those two booleans are enough to demonstrate the full spectrum of documented operator behavior — strict rejection, cautious deprioritization, and full acceptance — without building a policy language. There is no notion here of *how much* lower preference means, only that it is lower.

## Code Landmarks

### The module docstring

Read this before the code. It states the operational history directly: accepting-but-deprioritizing INVALID routes was common during early RPKI deployment, specifically to avoid blackholing traffic when a ROA was misconfigured. That is not a hypothetical edge case — it is why `reject_invalid` exists as a choice rather than RPKI validation always meaning "drop."

### `PolicyAction`

Three members, and the middle one's name is the whole lesson: `ACCEPT_LOWER_PREF`, not `DEPRIORITIZE`. Compare directly against `bgp/policy.py`'s `PolicyAction`.

### `apply_policy()`'s VALID branch

There is no boolean check here at all. VALID is unconditional `ACCEPT`. No policy stance in this model can turn a VALID route away — that asymmetry with INVALID and NOT_FOUND is worth noticing on its own.

### `apply_policy()`'s NOT_FOUND comment

"Most of the Internet is in this state, so rejecting it outright would break most of the Internet." This is the same absence-is-not-denial idea from `validate.py`'s NOT_FOUND reason, now carried forward into what policy is willing to do about it.

## Failure Questions

Use the source file to answer these:

1. Which single boolean field decides whether an INVALID verdict becomes `REJECT` versus `ACCEPT_LOWER_PREF`?
2. Which single boolean field decides whether a NOT_FOUND verdict becomes `ACCEPT_LOWER_PREF` versus `ACCEPT`?
3. Is there any `RoutingPolicy` configuration under which a VALID verdict produces something other than `ACCEPT`? Point to the line in `apply_policy()` that proves your answer.
4. According to the module docstring, why was accepting-but-deprioritizing INVALID routes common practice during early RPKI deployment?
5. According to the docstring and the NOT_FOUND branch's comment, what would happen to the Internet if NOT_FOUND routes were rejected wholesale?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/rpki/session_04_walkthrough.py
```

The walkthrough runs the same VALID, INVALID, and NOT_FOUND verdicts through two contrasting `RoutingPolicy` configurations side by side, so the headline lands directly: same verdict, different policy, different fate.

## Done When

The learner can say all of the following without looking at notes:

- "A verdict is a fact; `apply_policy()` is the only place that turns a fact into an action."
- "`reject_invalid` and `lower_pref_not_found` are the entire operator spectrum in this model — strict to permissive, two switches."
- "ACCEPT_LOWER_PREF is still an accept. The route stays in the RIB; it only loses tiebreaks."
- "NOT_FOUND is not denial — it is silence, and silence is common enough that rejecting it would break most of the Internet."

## References

- RFC 7115 (Origin Validation Operation Based on the Resource Public Key Infrastructure (RPKI))
- RFC 6482 (A Profile for Route Origin Authorizations (ROAs))
