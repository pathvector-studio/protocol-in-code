# Session 04 / Module 04: Origin Validation Is A Separate Decision

## Position

- Track: BGP
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/bgp/module-04/index.html`
- Source file: `src/protocol_in_code/bgp/validation.py`
- Walkthrough script: `examples/bgp/session_04_walkthrough.py`

## Core Question

How do we decide whether the origin AS is authorized, even after BGP has already selected a best path?

## Outcome

By the end of this session, the learner should be able to:

- explain why best path selection and origin authorization are different decisions
- explain what a VRP is compared to a BGP route
- explain why validation returns `valid`, `invalid`, or `not_found`
- explain how prefix coverage and max length affect the decision

## Read Order

1. Read `BGPRoute`
2. Read `VRP`
3. Read `vrp_covers_route()`
4. Read `validate_origin()`
5. Run `examples/bgp/session_04_walkthrough.py`
6. Explain why each route became `valid`, `invalid`, or `not_found`

## Read It Like Code

```python
covering_vrps = [vrp for vrp in vrps if vrp_covers_route(route, vrp)]

if not covering_vrps:
    return ValidationState.NOT_FOUND

if any(vrp.origin_as == route.origin_as for vrp in covering_vrps):
    return ValidationState.VALID

return ValidationState.INVALID
```

## Data That Matters

| Item | Why it matters |
|---|---|
| `route.prefix` | The route must be covered by some VRP before authorization can be judged. |
| `route.origin_as` | The route's origin AS is what gets validated. |
| `vrp.prefix` | The authorized prefix range. |
| `vrp.max_length` | Controls how specific a route may be while still being covered. |
| `vrp.origin_as` | The AS that is actually authorized. |

## Reading Lens

The important move in this session is to stop saying "this was the best path, so it must be fine" and start asking:

- is the route covered by any VRP?
- if covered, does the origin AS match?
- if there is no covering VRP, is that `invalid` or `not_found`?

## Design Choice

This session teaches origin validation as a separate concept after best-path so the learner can split `best` from `authorized`.

In integrated implementations, route validation may feed policy before final local installation or interact with selection at different points. The later pipeline lesson uses one such toy integration on purpose.

## Code Landmarks

### `BGPRoute`

This is the BGP-side information: prefix plus origin AS.

### `VRP`

This is the validated authorization-side information: prefix, max length, and authorized origin AS.

### `vrp_covers_route()`

This explains how prefix coverage works.

### `validate_origin()`

This is the main reading target for Session 04.

It answers:

- what `not_found` means
- what makes a route `valid`
- what makes a route `invalid`

## Failure Questions

Use the source file to answer these:

1. What happens if there are no covering VRPs?
2. What happens if a route is covered but the origin AS mismatches?
3. What happens if prefix coverage exists and the origin AS matches?
4. Why is `not_found` different from `invalid`?
5. Why does this logic still not validate the whole AS_PATH?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/bgp/session_04_walkthrough.py
```

The walkthrough prints valid, invalid, not_found, and max-length scenarios.

## Done When

The learner can say all of the following without looking at notes:

- "Best path selection and origin validation are separate decisions."
- "`not_found` means there was no covering VRP, not that the route was proven bad."
- "`invalid` means a covering VRP existed, but the origin AS did not match."
- "Origin validation checks the origin AS, not the full AS_PATH."

## References

- RFC 6482 Section 3
- RFC 6811 Section 2
- RFC 6811 Section 2.1
- RFC 8210 Sections 1-2
