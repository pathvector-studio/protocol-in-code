# Session 04 / Module 04: Pairs Are Checked in Priority Order

## Position

- Track: ICE
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/ice/module-04/index.html`
- Source file: `src/protocol_in_code/ice/checklist.py`
- Walkthrough script: `examples/ice/session_04_walkthrough.py`

## Core Question

Gathering (Session 03) produced a pile of maybes on each side. How does that pile become an ordered plan, and what decides which pair actually gets used?

## Outcome

By the end of this session, the learner should be able to:

- compute a candidate pair's priority using RFC 8445's min/max form and explain why it is symmetric
- explain what the "controlling" tie bit changes and what it does not
- read a formed checklist and say why it is sorted the way it is
- explain what `run_checklist` counts, and why "first success wins" is a simplification with a name

## Read Order

1. Read the module comment at the top of `checklist.py`
2. Read `pair_priority()`
3. Read `CandidatePair` and `Connectivity`
4. Read `form_checklist()`
5. Read `check_pair()`
6. Read `ChecklistResult` and `run_checklist()`
7. Run `examples/ice/session_04_walkthrough.py`

## Read It Like Code

```python
CandidatePair(
    local,
    remote,
    priority,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `local` / `remote` | The two candidates being tested together — one from each side's gathered pile. |
| `priority` | Computed once, at formation time, by `pair_priority()`. This is the sort key that turns a pile into a plan. |
| `Connectivity.reachable_type_pairs` | The caller-declared ground truth. Nothing in this module derives it — it stands in for whatever the NATs and topology actually allow. |
| `ChecklistResult.nominated` | The first pair that succeeded, or `None` if none did. |
| `ChecklistResult.checked` | How many pairs `run_checklist` actually looked at before stopping — not how many exist. |

## Decision Flow

```text
form_checklist(locals, remotes):
    cross every local candidate with every remote candidate
    compute pair_priority() for each pair
    sort all pairs by priority, HIGHEST FIRST -> that order IS the plan

run_checklist(pairs, reality):
    for each pair, in that fixed order:
        check_pair(pair, reality) -> SUCCEEDED or FAILED
        SUCCEEDED -> nominate this pair, stop immediately
    nothing succeeded -> nominated = None, checked = every pair
```

## Reading Lens

The important move in this session is to stop thinking of "priority" as a vague notion of preference and start asking, at every line:

- who computed this priority — the local side alone, or something both sides would compute identically?
- is this checklist walk asking a question about theory (what should work) or reality (what `Connectivity` says does work)?
- when `run_checklist` stops, did it stop because it found an answer, or because it ran out of pairs?

## Toy Model Boundary

Real ICE connectivity checks are STUN Binding requests carrying credentials and priority/USE-CANDIDATE attributes exchanged over the wire (RFC 8445 §7); this toy has no wire messages at all — `check_pair()` is a dictionary lookup against a caller-supplied `Connectivity`, standing in for "what actually happens if you tried." There is no trickle ICE here: `form_checklist()` assumes both candidate lists are already complete, not arriving incrementally. `controlling_is_larger` is the entire controlling/controlled model this toy implements — real ICE negotiates that role explicitly and can even resolve role conflicts (RFC 8445 §6.1.1); here it is just a boolean the caller asserts. And `run_checklist` stopping at the first success is "aggressive nomination" by name, in the source's own docstring — real ICE (§8) can keep checking after a success and swap the nomination later. This toy never does.

## Code Landmarks

### The module comment at the top

"Pairs are checked in priority order: gathering produced a pile of maybes, and this module turns that pile into an ordered plan and then executes it." That sentence is the whole session in one line — everything below either builds the order or executes it.

### `pair_priority()`

`lo = min(local_prio, remote_prio)`, `hi = max(local_prio, remote_prio)` — using min/max instead of "local's priority" and "remote's priority" directly is what makes both agents compute the identical number for the identical pair, regardless of which side is doing the computing. Only the `tie_bonus` — one bit — depends on which side is "controlling."

### `form_checklist()`

One list comprehension crosses every local candidate with every remote one; one `sorted(..., reverse=True)` turns the result into the plan. There is no separate "planning" data structure — the sort order on `pairs` is the plan.

### `check_pair()`

"Ask reality, not theory, whether this pair connects — ICE never predicts, it only tests." The function does not know why a pair might fail; it only knows whether `(local.ctype.value, remote.ctype.value)` is in `reality.reachable_type_pairs`.

### `run_checklist()`

The `enumerate(pairs, start=1)` loop is the entire nomination algorithm: walk in priority order, return on the first `SUCCEEDED`, otherwise report `checked = len(pairs)`. Compare that count against the checklist's total length to tell whether the loop stopped early or ran to exhaustion.

## Failure Questions

Use the source file to answer these:

1. `pair_priority(126, 100, controlling_is_larger=True)` and `pair_priority(100, 126, controlling_is_larger=True)` — are these equal? Which single term in the formula could make them differ, and under what condition?
2. What does `Connectivity.reachable_type_pairs` actually represent, and who is responsible for deciding what goes into it — `checklist.py`, or the caller?
3. If `run_checklist` returns `ChecklistResult(nominated=None, checked=9)` on a 9-pair checklist, what does that tell you happened to every single pair?
4. If `run_checklist` returns `checked=2` on a 9-pair checklist, what happened to pairs 3 through 9 — were they checked and failed, or never checked at all?
5. The docstring for `run_checklist` names its own simplification. What is that simplification called, and what would real ICE (RFC 8445 §8) be allowed to do that this toy never does?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/ice/session_04_walkthrough.py
```

The walkthrough checks that `pair_priority` is symmetric except for the tie bit, that `form_checklist` sorts descending, that `run_checklist` stops early on a first-pair success but walks the full list on a last-pair or no-pair success, and that `check_pair` is a direct reality lookup.

## Done When

The learner can say all of the following without looking at notes:

- "A checklist is not a decision procedure — it's a sorted list. The order is the entire plan; `run_checklist` just walks it."
- "Both agents compute the same pair priority for the same pair because the formula uses min/max, not 'mine' and 'theirs.'"
- "`checked` tells you how far the walk got, not how many pairs exist — and `nominated=None` with `checked` at the maximum means every pair failed."

## References

- RFC 8445 Section 6.1.2.3 (computing pair priority)
- RFC 8445 Section 8 (nominating pairs, including the "aggressive nomination" alternative this toy simplifies to)
