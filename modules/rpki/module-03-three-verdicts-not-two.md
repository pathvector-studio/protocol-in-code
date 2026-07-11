# Session 03 / Module 03: Three Verdicts, Not Two

## Position

- Track: RPKI
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/rpki/module-03/index.html`
- Source file: `src/protocol_in_code/rpki/validate.py`
- Walkthrough script: `examples/rpki/session_03_walkthrough.py`

## Core Question

Why does origin validation return three verdicts instead of a simple valid/invalid bool, and what exactly separates the two flavors of invalid?

## Outcome

By the end of this session, the learner should be able to:

- explain why `NOT_FOUND` is not a rejection
- explain the two different roads to `INVALID` and how the reason string tells them apart
- explain what `matched_roa` is set to for each verdict
- trace how `validate_origin()` builds on `covering.py`'s two separate checks instead of reintroducing a single combined one

## Read Order

1. Read the module docstring
2. Read `OriginVerdict`
3. Read `ValidationResult`
4. Read `validate_origin()`
5. Run `examples/rpki/session_03_walkthrough.py`

## Read It Like Code

```python
covering_roas = find_covering_roas(roas, announced_prefix)

if not covering_roas:
    return NOT_FOUND

for roa in covering_roas:
    if roa.origin_asn == origin_asn and within_max_length(announced_prefix, roa.max_length):
        return VALID

# covering ROAs exist, none validated: distinguish wrong-ASN from too-specific
return INVALID
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `roas` | The full candidate set; `validate_origin()` never assumes it has been pre-filtered. |
| `announced_prefix` | The single address range being judged. |
| `origin_asn` | The AS actually originating the announcement — checked against each covering ROA's `origin_asn`. |
| `verdict` | One of three `OriginVerdict` values, never a bool. |
| `matched_roa` | Set only on `VALID`; `None` for both `INVALID` and `NOT_FOUND`. |
| `reason` | A human-readable string whose wording differs by verdict and, within `INVALID`, by which of the two failure roads was taken. |

## Decision Flow

```text
no covering ROA at all                                    -> NOT_FOUND
covering ROA(s) exist, one has right ASN and right length  -> VALID
covering ROA(s) exist, right ASN exists but too specific    -> INVALID (reason cites "/NN")
covering ROA(s) exist, none has the right ASN               -> INVALID (reason cites "not AS<asn>")
```

## Reading Lens

This session deepens `bgp/validation.py`'s Session 04 (`ValidationState`: `VALID` / `INVALID` / `NOT_FOUND`). The verdict names mirror that module on purpose — same three-way shape, same headline claim that `NOT_FOUND` is not a denial. What is new here is the prefix math sitting underneath the verdict. BGP session 04's `vrp_covers_route()` folds range containment and max-length into a single check; this track's session 02 split that into `covers()` and `within_max_length()`, and this session is where the split pays off: `validate_origin()` calls `find_covering_roas()` (range only) and then, only for ROAs that pass that filter, separately checks ASN match and `within_max_length()`. That is what makes it possible to tell an operator *which* of the two prefix-math checks failed — wrong ASN or too specific — instead of just "invalid."

- did any ROA cover this address range at all? If not, stop — that is `NOT_FOUND`, not `INVALID`.
- among the covering ROAs, does any one of them have both the right `origin_asn` and satisfy `within_max_length()`?
- if none does, is the reason "the right AS announced too specifically" or "no covering ROA authorizes this AS at all"? Read the two reason-string branches to see which one fires.

## Toy Model Boundary

This module validates a single announcement against a fixed set of ROAs, one call at a time — there is no session state, no batch validation, and no interaction with best-path selection or router policy (that integration point is the same one BGP session 04's design-choice note gestures at). It also inherits session 01 and 02's boundaries: IPv4 only, unsigned `Roa` payloads, no multi-prefix ROAs.

## Code Landmarks

### `OriginVerdict`

Three values, mirroring `bgp/validation.py`'s `ValidationState`. Read the module docstring's opening comment — the cross-reference to BGP session 04 is deliberate, not incidental.

### `ValidationResult`

`matched_roa` is the tell: it is populated only in the `VALID` branch. Both `INVALID` and `NOT_FOUND` return `matched_roa=None`, even though `INVALID` implies a covering ROA existed — the field name is "matched," not "covering."

### `validate_origin()`

The main reading target. Notice the order of operations: `find_covering_roas()` runs first and unconditionally. Only if that set is non-empty does the function even ask about `origin_asn` or `within_max_length()`. The final `if right_asn_too_specific:` branch is where the two `INVALID` reasons diverge — read both string-building branches side by side.

## Failure Questions

Use the source file to answer these:

1. `roas` is empty. What verdict comes back, and what does the reason string say about what an empty result means?
2. A covering ROA exists with the right `origin_asn=65001` but `max_length=23`, and the announcement is a `/24`. What verdict, and what number appears in the reason string?
3. Two covering ROAs exist, both authorizing `origin_asn=65010`, neither matching the announced `origin_asn=65099`. What substring does the reason string contain, and which loop variable produces it?
4. Which check runs first inside `validate_origin()` — the ASN match or `within_max_length()`? Does the order matter for the final verdict?
5. `matched_roa` is `None`. Can you tell from that fact alone whether the verdict was `INVALID` or `NOT_FOUND`? What field would you need instead?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/rpki/session_03_walkthrough.py
```

The walkthrough validates the same announcement, `203.0.113.0/24` from AS65001, against four different ROA sets — producing `VALID`, an over-specific `INVALID`, a wrong-ASN `INVALID`, and `NOT_FOUND` — and then repeats the point as a single headline: one announcement, three ROA sets, three different verdicts.

## Done When

The learner can say all of the following without looking at notes:

- "`NOT_FOUND` means no ROA covers this range — silence, not a lie."
- "`INVALID` has two roads: wrong ASN, or right ASN announced too specifically — the reason string tells you which."
- "`matched_roa` is set only for `VALID`."
- "This is the same tri-state as BGP session 04, now built on `covering.py`'s explicit range-then-length checks instead of one combined comparison."

## References

- RFC 6811 Section 2 (RPKI-based origin validation, the VALID/INVALID/NotFound states)
- RFC 6482 Section 3 (ROA content this verdict is computed from)
- RFC 7115 (origin validation operational considerations)
