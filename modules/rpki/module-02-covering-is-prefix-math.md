# Session 02 / Module 02: Covering Is Prefix Math

## Position

- Track: RPKI
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/rpki/module-02/index.html`
- Source file: `src/protocol_in_code/rpki/covering.py`
- Walkthrough script: `examples/rpki/session_02_walkthrough.py`

## Core Question

"Does this ROA say anything about this announcement?" is really two separate questions — what are they, and why is conflating them the classic operator mistake?

## Outcome

By the end of this session, the learner should be able to:

- explain what `covers()` checks and what it deliberately ignores
- explain what `within_max_length()` checks and why it is a separate function
- give an example of a ROA that covers an announcement's address range but still rejects it for specificity
- explain what `find_covering_roas()` filters on, and what it does not filter on

## Read Order

1. Read the module docstring
2. Read `covers()`
3. Read `within_max_length()`
4. Read `find_covering_roas()`
5. Run `examples/rpki/session_02_walkthrough.py`

## Read It Like Code

```python
roa_net = ip_network(roa_prefix)
announced_net = ip_network(announced_prefix)
return announced_net.subnet_of(roa_net)
```

## Fields That Matter

| Item | Why it matters |
|---|---|
| `roa_prefix` | The address range the ROA authorizes. The container in the containment question. |
| `announced_prefix` | The address range actually being announced. The candidate in the containment question. |
| `max_length` | Not an address-range fact at all — a specificity ceiling, checked by a completely separate function. |

## Decision Flow

```text
covers(roa_prefix, announced_prefix) is False   -> ROA says nothing about this announcement, full stop
covers(...) is True, within_max_length(...) is False -> ROA's range matches, but announcement is too specific
covers(...) is True, within_max_length(...) is True  -> both prefix-math checks pass
```

## Reading Lens

The important move in this session is to stop treating "does this ROA match this announcement" as one yes/no question and start asking two:

- is the announced address range even inside the ROA's address range?
- if it is, is the announcement's prefix length within what the ROA's `max_length` allows?

`covers()` answers only the first question — pure address-range containment via `subnet_of()`, with no opinion on specificity. A `/8` ROA "covers" a `/24` announcement in this sense even if the ROA's `max_length` never authorized anything narrower than `/9`. That gap between "covers" and "is specific enough" is precisely why `within_max_length()` is kept as its own visible function instead of being folded into `covers()` — conflating the two is the classic operator mistake the module docstring names directly. `bgp/validation.py`'s `vrp_covers_route()` (BGP session 04) does both checks in one function; this session pulls that single check apart into the two questions it is actually made of, and session 03's `validate.py` recombines them explicitly instead of implicitly.

## Toy Model Boundary

Real RPKI validators work against ROAs that can authorize more than one prefix per object and must handle both address families. This toy keeps each `Roa` to a single IPv4 prefix and does no aggregation across ROAs — `find_covering_roas()` returns every covering ROA as a flat tuple, with no attempt to merge or rank them. That ranking (and the wrong-ASN-vs-too-specific classification) is session 03's job, not this one.

## Code Landmarks

### `covers()`

The whole function is one line of logic: `announced_net.subnet_of(roa_net)`. Read the docstring's disclaimer carefully — this says nothing about `max_length`. A `/8` ROA covers a `/24` announcement here regardless of what the ROA's `max_length` says.

### `within_max_length()`

Deliberately explicit rather than folded into `covers()`: `prefixlen <= max_length`, nothing else. The docstring gives the exact failure case: a `/24` announcement under `max_length=23` fails this even though it passes `covers()`.

### `find_covering_roas()`

Filters on `covers()` alone — range only, not length. The name is precise: "covering" is an address-range relationship in this module, not a validity verdict. A ROA can be in this function's output and still reject the announcement once `within_max_length()` runs.

## Failure Questions

Use the source file to answer these:

1. A ROA authorizes `10.0.0.0/8` with `max_length=8`. An announcement is `10.1.0.0/16`. Does `covers()` return `True` or `False`? Does `within_max_length()`?
2. Why does `covers()` never look at `max_length` at all — which function owns that check?
3. `within_max_length("203.0.113.0/24", 23)` — is the boundary `<=` or `<`? What does that decide for a `/23` announcement under `max_length=23`?
4. `find_covering_roas()` is given three ROAs, only two of which have address ranges containing the announcement. What does it return, and on what basis were the other one excluded?
5. Why does the module keep `covers()` and `within_max_length()` as two functions instead of one function that returns a single bool?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/rpki/session_02_walkthrough.py
```

The walkthrough checks address-range containment on its own, checks the max_length boundary on its own, and then filters three ROAs down to the ones whose range actually covers the announcement.

## Done When

The learner can say all of the following without looking at notes:

- "`covers()` is pure address-range containment — it has no opinion on specificity."
- "`within_max_length()` is `prefixlen <= max_length`, kept separate on purpose."
- "A ROA can cover an announcement's range and still reject it for being too specific — that combination is the classic operator mistake."
- "`find_covering_roas()` filters on range only; it does not decide validity."

## References

- RFC 6811 Section 2 (RPKI-based origin validation, the covering relationship)
