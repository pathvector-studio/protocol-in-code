# Session 02 / Module 02: Election Is a Comparison Function, Five Times

## Position

- Track: Same Shape
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/meta/module-02/index.html`
- Source file: `src/protocol_in_code/meta/election.py`
- Walkthrough script: `examples/meta/session_02_walkthrough.py`

## Core Question

BGP, OSPF, RIP, VRRP, and STP each hold an "election" among candidates that never actually votes — so what's really happening when a router "elects" a best path, a designated router, a preferred route, a master, or a root bridge?

## Outcome

By the end of this session, the learner should be able to:

- state the one operation ("build a comparison key per candidate, take an extreme") that all five elections reduce to
- name which four of the five take the max of their key, and which one takes the min
- explain, in one sentence, why the STP inversion is a classic source of bugs when porting election logic between modules
- point to the real comparison key tuple each package actually compares candidates on

## Read Order

1. Read the module docstring at the top of `election.py`
2. Read `ElectionDemo`
3. Read `demonstrate_all()` stanza by stanza — BGP, then OSPF, then RIP, then VRRP, then STP
4. Read `the_inversion()` and its docstring
5. Cross-read `stp/root_election.py`'s own module docstring, which `the_inversion()` cites directly
6. Run `examples/meta/session_02_walkthrough.py`

## Read It Like Code

```python
ElectionDemo(
    protocol,
    direction,
    key_description,
    winner,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `protocol` | Which of the five real packages ran this election — `bgp`, `ospf`, `rip`, `vrrp`, or `stp`. |
| `direction` | `"highest wins"` for four of the five, `"lowest wins"` for exactly one (STP). This is the field the whole session pivots on. |
| `key_description` | The literal comparison key tuple the real package's selection function sorts or compares on — not a re-derivation of it. |
| `winner` | The identifying field of the candidate the real function actually returned — a next-hop, a router ID, a name, a MAC address. |

## Decision Flow

```text
demonstrate_all(), each stanza:
  1. build a tuple of real candidate objects (PathCandidate, InterfaceCandidate, RipRoute, VrrpRouter, BridgeId)
  2. call the package's own real selection function on that tuple
  3. record its direction: max-of-key ("highest wins") or min-of-key ("lowest wins")
  4. record the winner's own identifying field, straight from the real return value

the_inversion(): one sentence, stated outright —
  OSPF, RIP, VRRP  -> max() of a (priority-or-metric, id) - shaped key -> highest wins
  STP              -> min() of the SAME SHAPE of key                    -> lowest wins
  same shape, opposite sign -> swap max()/min() while porting and every rank flips silently
```

## Reading Lens

The important move in this session is to stop asking "who won this election?" and start asking, for every one of the five stanzas:

- what tuple is actually being compared — not the field names, the *order* they're compared in?
- does this package take the max of that tuple, or the min?
- if I swapped this package's `max()`/`min()` for its opposite, which candidate would win instead, and would the bug be silent or loud?

RIP's "lowest wins" and STP's "lowest wins" look identical in the `direction` field, but they're testing different things — RIP's key is a hop-count *metric* (fewer hops is better, an intuitive minimum), while STP's key is a *tiebroken identity* (`(priority, mac)`, where "lower ID" is an arbitrary convention with no distance intuition behind it, as `stp/root_election.py`'s own docstring says outright). Don't let the shared `direction` string flatten that difference.

## Toy Model Boundary

This session runs five real selection functions on three hand-built candidates each — it is a demonstration of the comparison-and-extreme shape, not proof that BGP best-path selection, OSPF DR election, RIP route preference, VRRP mastership, and STP root election are interchangeable. Each package's actual comparison key carries protocol-specific fields this file only shows the shape of: BGP's real tie chain (`weight`, `local_pref`, `as_path` length, origin type, `next_hop`) has more steps than OSPF's two-field `(priority, router_id)`, and none of the five toy candidate sets here model what happens when two candidates tie on every field.

## Code Landmarks

### The module docstring

Names the punchline before any code runs: "Four of the five take the max (highest key wins); STP alone takes the min (lowest key wins) — the deliberate inversion this file's second function names." Read `demonstrate_all()` already knowing which stanza is the odd one out.

### The BGP stanza's `key_description`

`"(weight, local_pref, -len(as_path), -origin_type, next_hop)"` — the negative signs on `as_path` length and origin type are doing real work: BGP prefers *shorter* AS paths and *lower* origin type codes, but the overall tie chain still resolves by taking the max of the whole tuple. Negating the fields that want "lower is better" is how a single `max()` call implements a comparison chain with mixed directions.

### `the_inversion()`'s docstring

Names the failure mode directly: "swap max() for min() (or vice versa) while porting election logic between these modules and every candidate's rank silently flips." This is not a hypothetical — it's the same warning `stp/root_election.py`'s own module docstring gives, cited by name in this function's docstring.

### The STP stanza's candidate set

Two of the three `BridgeId` candidates share `priority=4096`; only the MAC address breaks the tie. This is deliberately the same tie-break shape as OSPF's stanza (`priority=10` shared by two of three `InterfaceCandidate`s) — same shape of tiebreak, opposite direction of extreme.

## Failure Questions

Use the source file to answer these:

1. Which packages' comparison key is described in `demonstrate_all()` as a tuple containing a negative sign on one of its fields, and what does that negative sign accomplish inside a single `max()` call?
2. `the_inversion()`'s docstring says "OSPF, RIP, and VRRP" take the max — but the RIP stanza's `direction` field reads `"lowest wins"`. Is this a contradiction? What is RIP actually taking the max or min *of*, and how does that reconcile with the docstring's claim?
3. Which two rows in `demonstrate_all()` share the exact same `direction` string, and what is different about what their `key_description` fields are actually comparing?
4. Why does the STP stanza's candidate list include two `BridgeId`s with the same `priority` but different MAC addresses, and what does the resulting winner tell you about which field breaks the tie?
5. If you swapped `elect_root()`'s `min()` for a `max()` in `stp/root_election.py`, which of the three `BridgeId` candidates in this file's STP stanza would become the new root, and would that new winner be silently wrong or obviously wrong?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/meta/session_02_walkthrough.py
```

The walkthrough calls `demonstrate_all()`, checks it returns exactly 5 rows, confirms both `"highest wins"` and `"lowest wins"` directions are present, checks every row's `winner` field is non-empty, and confirms `the_inversion()`'s return value names both STP and VRRP by substring.

## Done When

The learner can say all of the following without looking at notes:

- "Every election in this course reduces to building a comparison key per candidate and taking an extreme — the only thing that varies is the key's shape and which extreme."
- "OSPF, RIP, and VRRP take the max of their key; STP alone takes the min of the same shape of key — same shape, opposite sign."
- "Swapping max() for min() while porting election logic between these modules is the classic bug this inversion sets up, because the rank flips silently, not loudly."

## References

- `modules/bgp/module-03-best-path-if-statements.md` — BGP best-path selection
- `modules/ospf/module-03-dr-bdr-election.md` — OSPF designated router election
- `modules/rip/module-01-a-route-is-a-rumor-with-a-distance.md` — RIP route preference
- `modules/ha/module-01-the-highest-priority-speaks.md` — VRRP master election
- `modules/stp/module-01-the-root-is-the-lowest-id.md` — STP root election, the inversion
