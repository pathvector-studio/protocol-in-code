# Session 05 / Module 05: Build the Toy Validator Loop

## Position

- Track: RPKI
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/rpki/module-05/index.html`
- Source file: `src/protocol_in_code/rpki/validator_loop.py`
- Walkthrough script: `examples/rpki/session_05_walkthrough.py`

## Core Question

What does a real RPKI validator's whole job look like when loading ROAs, checking one announcement, and sweeping a whole route table are wired into a single object instead of four separate demos?

## Outcome

By the end of this session, the learner should be able to:

- name every module `ToyValidator` imports and which earlier session taught it
- explain what `load_roas()` does with a malformed ROA, and why that is a skip and not a crash
- trace `check()`'s covering -> validate -> policy pipeline and say what each of its three trace lines records
- explain what `evaluate_table()` counts, and why its totals must equal the number of announcements it was given
- run the validator over `demo_roas()` and a small announcement table, reading the trace as the source of truth

## Read Order

1. Read the module docstring at the top of `validator_loop.py`
2. Read `CheckResult`
3. Read `TableReport`
4. Read `ToyValidator`'s field list
5. Read `load_roas()`
6. Read `check()`
7. Read `demo_roas()`
8. Read `evaluate_table()`
9. Run `examples/rpki/session_05_walkthrough.py`

## Read It Like Code

```python
ToyValidator(
    roas,
    policy,
    trace,
)
```

## Parts List

Every function `validator_loop.py` imports was taught by an earlier session in this track. The capstone's only new code is the loop that wires them together and the trace that explains it afterward.

| Import | Session that taught it | What it contributes to `ToyValidator` |
|---|---|---|
| `roa.Roa`, `RoaValidity`, `validate_roa` | 01 | The permission-slip shape and the well-formedness check `load_roas()` runs on every candidate before accepting it. |
| `covering.find_covering_roas` | 02 | The prefix-range filter `check()` runs first, so the trace can record how many ROAs even apply before validation runs. |
| `validate.OriginVerdict`, `ValidationResult`, `validate_origin` | 03 | The VALID / INVALID / NOT_FOUND tri-state; `check()`'s second trace line is this session's `reason` string verbatim. |
| `policy.PolicyAction`, `PolicyDecision`, `RoutingPolicy`, `apply_policy` | 04 | `self.policy`; `check()`'s third trace line is the concrete action and note this session's `apply_policy()` produced. |

Session 04 (`bgp/module-04-origin-validation.md`) and Session 05 (`bgp/module-05-policy-after-validation.md`) of the **BGP track** are the upstream consumers of these verdicts: a real BGP speaker calls something shaped like `ToyValidator.check()` for every route it hears, then feeds the resulting `PolicyAction` into best-path selection. This module is the RPKI side of that boundary; the BGP track is what happens on the other side of it.

## Decision Flow

```text
load_roas(candidates):
  for each candidate:
    validate_roa(candidate)
      VALID     -> append to accepted, trace "load: accepted ..."
      otherwise -> skip, trace "load: skipped ... (<reason>)"
  self.roas = self.roas + accepted

check(prefix, asn):
  1. find_covering_roas(self.roas, prefix)      -> trace "N covering ROA(s)"
  2. validate_origin(self.roas, prefix, asn)     -> trace "verdict=... (<reason>)"
  3. apply_policy(verdict, self.policy)          -> trace "action=... (<note>)"
  return CheckResult(verdict, action, trace_slice)

evaluate_table(validator, announcements):
  for each (prefix, asn) in announcements:
    result = validator.check(prefix, asn)
    verdict_counts[result.verdict] += 1
    action_counts[result.action]   += 1
  return TableReport(total=len(announcements), verdict_counts, action_counts)
```

## Reading Lens

The important move in this session is to stop reading `roa.py`, `covering.py`, `validate.py`, and `policy.py` as four separate lessons and start asking, at every line of `check()`:

- which of the four earlier sessions' functions is doing the actual work on this line?
- what did `self.trace` just gain, and would that one line alone tell an operator what happened, without re-running anything?
- is `check()` deciding anything itself, or is it only sequencing decisions that Sessions 01-04 already know how to make?

This is the same posture Session 05 of the TCP track (`module-11-build-the-toy-tcp-loop.md`) asks for: a capstone earns no credit for new logic, only for wiring existing logic into something that runs continuously and stays explainable.

## Toy Model Boundary

A real RPKI validator (routinator, rpki-client, OctoRPKI, and the routers that consume their output) talks to routers over the RPKI-to-Router protocol (RTR, RFC 8210) — a long-lived session that pushes Validated ROA Payload (VRP) updates as *deltas*, not full reloads, and caches the current VRP set so every route doesn't require re-parsing every ROA from scratch. `ToyValidator` has none of that: `load_roas()` is called once, synchronously, with a full candidate set already in memory; `check()` is a plain function call with no session state beyond `self.roas`, `self.policy`, and `self.trace`; and there is no cache invalidation, no incremental update, and no network protocol anywhere in this file. `roas` is a Python tuple rebuilt by concatenation on every `load_roas()` call, not an indexed store — fine for a demo table of four ROAs, not fine for the roughly one million ROAs a real cache holds today.

## Code Landmarks

### The module docstring

States the capstone's whole thesis directly: "a real RPKI validator is just this loop run continuously." Read it before the class — it is the frame for everything below.

### `load_roas()`

The only place malformed input is handled instead of assumed away. A candidate ROA that fails `validate_roa()` is skipped, not raised — the trace line still records it, tagged with the `RoaValidity` reason, so a bad ROA in the input feed does not stop the rest of the set from loading.

### `check()`'s three trace lines

One line per stage: covering count, verdict plus reason, action plus note. Each line is generated by a different earlier session's code (`covering.py`, `validate.py`, `policy.py` respectively) — `check()` itself contributes no reasoning, only sequencing and the trace calls.

### `demo_roas()`

Four ROAs, by design: one clean VALID target, one wrong-ASN/too-specific target for INVALID, one deliberately uncovered range for NOT_FOUND, and one malformed prefix (`"not-a-prefix"`) that exists purely to exercise `load_roas()`'s skip path.

### `evaluate_table()`

The route-table sweep a real validator performs continuously: call `check()` once per announcement, tally `verdict_counts` and `action_counts`, and report a `total` that must equal the number of announcements handed in — nothing here filters or drops an announcement before it is counted.

## Failure Questions

Use the source file to answer these:

1. In `load_roas()`, what happens to a candidate `Roa` whose prefix string fails to parse — does it raise, and what does the trace record for it?
2. In `check()`, which of the three trace lines is produced directly from `ValidationResult.reason`, and which is produced from `PolicyDecision.note`?
3. If `self.roas` is empty when `check()` runs, what verdict does `validate_origin()` return, and which line in `check()`'s trace reflects that before the verdict line even runs?
4. What three fields does `TableReport` hold, and does `evaluate_table()` ever produce a `total` that differs from `len(announcements)`?
5. `demo_roas()` returns four `Roa` objects. According to its own docstring, which one is not meant to survive `load_roas()`, and why?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/rpki/session_05_walkthrough.py
```

The walkthrough loads `demo_roas()` into a fresh `ToyValidator` and shows the malformed ROA's skip line in the trace, runs one VALID, one INVALID, and one NOT_FOUND announcement through `check()` and asserts each result's verdict and action, then runs `evaluate_table()` over four announcements and checks `total == 4` against the tallied `verdict_counts`, and finally checks that a `check()` call's `trace_slice` is non-empty and contains its covering-count line.

## Done When

The learner can say all of the following without looking at notes:

- "`ToyValidator` introduces no new validation logic — `load_roas()` and `check()` only sequence Sessions 01 through 04."
- "A malformed ROA is skipped at load time, traced, and never reaches `check()` — it does not stop the rest of the set from loading."
- "`check()`'s three trace lines are covering count, verdict plus reason, and action plus note, produced by three different earlier modules in that order."
- "`evaluate_table()`'s total always equals the number of announcements handed in; nothing in the sweep drops one silently."
- "A real validator adds RTR, delta updates, and VRP caching on top of exactly this loop — none of which this toy needs to teach the loop itself."

## References

- RFC 6811 (BGP Prefix Origin Validation)
- RFC 6482 (A Profile for Route Origin Authorizations (ROAs))
