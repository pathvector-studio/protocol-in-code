# Session 03 / Module 03: Best Path Selection As If Statements

## Position

- Track: BGP
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/bgp/module-03/index.html`
- Source file: `src/protocol_in_code/bgp/best_path.py`
- Walkthrough script: `examples/bgp/session_03_walkthrough.py`

## Core Question

Why does one BGP path become best, and which comparison produced the winner first?

## Outcome

By the end of this session, the learner should be able to:

- explain why best path logic only matters after multiple paths exist
- explain why comparison order changes the result
- identify the first condition that produced the winner
- explain why `best` does not automatically mean `authorized` or `safe`

## Read Order

1. Read `PathCandidate`
2. Read `_is_better()`
3. Read `select_best_path()`
4. Run `examples/bgp/session_03_walkthrough.py`
5. Explain why each scenario picked its winner

## Read It Like Code

```python
if candidate.weight != current.weight:
    return candidate.weight > current.weight
if candidate.local_pref != current.local_pref:
    return candidate.local_pref > current.local_pref
if len(candidate.as_path) != len(current.as_path):
    return len(candidate.as_path) < len(current.as_path)
if candidate.origin_type != current.origin_type:
    return candidate.origin_type < current.origin_type
return candidate.next_hop < current.next_hop
```

## Simplification Note

This comparison chain mixes protocol-facing and teaching-facing fields on purpose.

`weight` is a vendor-local preference, not an RFC 4271 path attribute, and the final `next_hop` comparison is only a deterministic fallback for the toy model. Read this lesson as "ordered branches decide the winner," not as a literal full RFC tie-break chain.

## Data That Matters

| Field | Why it matters |
|---|---|
| `prefix` | You can only compare paths for the same destination. |
| `weight` | The first branch in this simplified decision logic. |
| `local_pref` | The next branch when weight is tied. |
| `as_path` | Path length becomes the next tiebreaker. |
| `origin_type` | Another ordered comparison after AS path length. |
| `next_hop` | Final fallback tiebreaker in this code. |

## Reading Lens

The important move in this session is to stop saying "BGP preferred this one somehow" and start asking:

- what was the first differing field?
- which branch fired first?
- what comparisons were skipped because a winner was already decided?

## Code Landmarks

### `PathCandidate`

This tells you what comparison data a path carries.

### `_is_better()`

This is the main reading target for Session 03.

It answers:

- which field is checked first
- what happens when fields tie
- how the first successful branch decides the winner

### `select_best_path()`

This shows how pairwise comparisons collapse multiple candidates down to one best path.

## Failure Questions

Use the source file to answer these:

1. What happens if there are zero paths?
2. What happens if the compared paths do not share the same prefix?
3. Why can a shorter AS path lose when local preference is lower?
4. Which later comparisons never run once an earlier branch decides the result?
5. Why does `best` still not answer whether the route is authorized?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/bgp/session_03_walkthrough.py
```

The walkthrough prints several competing-path scenarios and tells you which path won, plus the first reason that decided it.

## Done When

The learner can say all of the following without looking at notes:

- "Best path logic starts only after multiple paths exist for the same prefix."
- "The first differing comparison decides the winner."
- "A shorter AS path can still lose if an earlier field already gave another path the win."
- "Best path selection is not the same thing as route authorization or leak detection."

## References

- RFC 4271 Section 3
- RFC 4271 Section 5
- RFC 4271 Section 9
- RFC 7908
