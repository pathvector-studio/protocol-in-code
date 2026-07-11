# Session 03 / Module 03: Three States Beat Two

## Position

- Track: Same Shape
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/meta/module-03/index.html`
- Source file: `src/protocol_in_code/meta/tristate.py`
- Walkthrough script: `examples/meta/session_03_walkthrough.py`

## Core Question

RPKI, BFD, ARP, and DNSSEC each refused to model their central verdict as a boolean — so what is the third state actually buying each of them, and is it the same purchase every time?

## Outcome

By the end of this session, the learner should be able to:

- name the third state in each of the four protocols and what it means operationally, in that package's own words
- state the one shared lesson `why_not_bool()` draws across all four
- explain why DNSSEC's three `BOGUS_*` members collapse into one bucket for this comparison, and what distinction is lost by doing so
- explain why RPKI's third state is spelled `NOT_FOUND` rather than `UNKNOWN` or `MAYBE`

## Read Order

1. Read the module docstring at the top of `tristate.py`
2. Read `TristateDemo`
3. Read `demonstrate_all()` stanza by stanza — RPKI, then BFD, then ARP, then DNSSEC
4. Read the comment above the DNSSEC stanza explaining the `BOGUS_*` collapse
5. Read `why_not_bool()` and its docstring
6. Run `examples/meta/session_03_walkthrough.py`

## Read It Like Code

```python
TristateDemo(
    protocol,
    states,
    third_state_meaning,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `protocol` | Which of the four real packages this row describes — `rpki`, `bfd`, `arp`, or `dnssec`. |
| `states` | A 3-tuple of the real enum's `.value` strings, in the package's own defined order — always exactly three, never collapsed to two. |
| `third_state_meaning` | The operational reading of the middle state, in prose, sourced from that package's own semantics — not a generic "unknown" gloss. |

## Decision Flow

```text
for each protocol, the question is never "yes or no?" but "which flavor of no?":
  rpki:    VALID     / INVALID  / NOT_FOUND  -> rejected vs. no ROA published at all
  bfd:     DOWN      / INIT     / UP         -> confirmed dead vs. half-agreed, still negotiating
  arp:     INCOMPLETE/ REACHABLE/ STALE      -> never resolved vs. resolved but past its confidence window
  dnssec:  SECURE    / BOGUS*   / INSECURE   -> proof failed vs. proof was never attempted (no DS at all)
```

## Reading Lens

The important move in this session is to stop asking "what are the three states called?" and start asking, for every protocol:

- which of the three states is the "yes," which is the "confirmed no," and which is the disputed middle one?
- what specific action does the middle state license that neither of the other two would — keep negotiating, keep forwarding while re-confirming, fall back to unauthenticated trust?
- if this protocol had shipped with a boolean instead, which two situations would have been silently conflated, and which wrong action would that conflation cause?

`why_not_bool()` names the general form of this question directly: an active, proven rejection versus a mere absence of proof. Every stanza in this session is an instance of that same distinction, spelled differently by four different standards bodies.

## Toy Model Boundary

This session compares four real enums side by side, but it does not model every transition between their states — `demonstrate_all()` reads each protocol's already-defined enum members and states what they mean; it does not run a validator, a BFD session, an ARP cache, or a DNSSEC chain walk to *produce* a verdict. `arp/cache.py`'s state machine, in particular, has real transition timing (`REACHABLE_SECONDS`) this file doesn't exercise — see Session 01's `common_shape()` for where ARP's degrade-not-delete behavior is actually demonstrated in motion.

The DNSSEC row is the clearest place this session's "three states" framing is a simplification stated on purpose, not an oversight: `ChainOutcome` has five real members (`SECURE`, `INSECURE`, and three distinct `BOGUS_*` flavors), and this file collapses three of them into one displayed bucket, with a comment explaining exactly why — for a three-state comparison, all three `BOGUS_*` flavors are still "a proof that failed, just at a different hop."

## Code Landmarks

### The module docstring

States the shared mechanism before any code runs: "in every case 'no' has two different flavors that call for two different actions, so the type system carries a third state instead of forcing the caller to re-derive the distinction from context." Every stanza below is an instantiation of that sentence.

### The comment above the DNSSEC stanza

Explains a real discrepancy between this file's "three states" framing and the actual enum: "`ChainOutcome` actually has three `BOGUS_*` flavors ... distinguishing WHERE the chain broke. For this three-state comparison they collapse to one 'BOGUS' bucket." This is the one stanza in the session where the source is explicit that its own comparison is a simplification.

### The RPKI stanza's `third_state_meaning`

"absence of a ROA is not a denial, it just means nobody published a permission slip" — echoes RPKI's own module framing (a ROA as a permission slip) from earlier in the course, reusing the metaphor rather than inventing a new one for this retrospective.

### `why_not_bool()`'s docstring

Gives the one-line version of all four rows at once, then immediately grounds it in each protocol's real action: "reject the route versus fall back to unauthenticated trust, tear down the session versus keep negotiating, evict the neighbor versus keep forwarding while re-confirming." Three concrete action-pairs for three of the four protocols — DNSSEC's own action-pair (trust the chain vs. treat as unsigned) is the one left as an exercise.

## Failure Questions

Use the source file to answer these:

1. Which package's outcome enum appears in the DNSSEC row's `states` tuple as a synthesized string rather than a single real enum member's `.value` — and what does that synthesized string contain?
2. `arp/cache.py` is one of the four protocols compared in this session. Why is ARP's third state `STALE` rather than something that means "never resolved," and which of the *other* three protocols' third states does `STALE` most resemble in spirit?
3. RPKI's third state is `NOT_FOUND`. According to `third_state_meaning`, what is the operational difference between `NOT_FOUND` and `INVALID` — what would a caller do differently for each?
4. BFD's third state is `INIT`, described as "half-agreed." Which of BFD's *other* two states does a session in `INIT` eventually move to, and does it ever move there without passing through `INIT`?
5. Why does the comment above the DNSSEC stanza say the three `BOGUS_*` flavors are "still a proof that failed, just at a different hop" — what does "at a different hop" mean for a chain-of-trust validator, and why doesn't this file distinguish them as three separate third-and-fourth-and-fifth states?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/meta/session_03_walkthrough.py
```

The walkthrough calls `demonstrate_all()`, checks it returns exactly 4 rows, confirms every row's `states` tuple has exactly 3 entries, confirms all 4 `third_state_meaning` strings are distinct, and confirms `why_not_bool()` returns a non-empty string containing both "two" and "flavors."

## Done When

The learner can say all of the following without looking at notes:

- "RPKI, BFD, ARP, and DNSSEC each refused to collapse to a boolean because 'no' has two different flavors that demand different actions."
- "The third state is never a generic 'unknown' — it's a specific, named condition with its own action: half-agreed, usable-but-doubted, no-proof-published, no-chain-attempted."
- "DNSSEC actually has five outcomes, not three — this session's three-state framing deliberately collapses three BOGUS flavors into one bucket for the comparison."

## References

- `modules/rpki/module-03-three-verdicts-not-two.md` — RPKI's `VALID`/`INVALID`/`NOT_FOUND`
- `modules/ha/module-03-three-states-both-directions.md` — BFD's `DOWN`/`INIT`/`UP`
- `modules/arp/module-01-the-cache-has-moods.md` — ARP's `INCOMPLETE`/`REACHABLE`/`STALE`
- `modules/dnssec/module-04-validation-walks-up-the-tree.md` — DNSSEC's `SECURE`/`BOGUS_*`/`INSECURE`
