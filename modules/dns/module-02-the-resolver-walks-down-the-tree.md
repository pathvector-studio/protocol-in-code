# Session 02 / Module 02: The Resolver Walks Down the Tree

## Position

- Track: DNS
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/dns/module-02/index.html`
- Source file: `src/protocol_in_code/dns/walk.py`
- Walkthrough script: `examples/dns/session_02_walkthrough.py`

## Core Question

How does a resolver get from the root to an answer, and what does each hop actually decide?

## Outcome

By the end of this session, the learner should be able to:

- describe iterative resolution as a loop, not a lookup
- explain what a zone knows directly versus what it delegates
- explain why the walk picks the most specific matching delegation
- name the three ways the walk can end without an answer

## Read Order

1. Read `Zone`
2. Read `zone_covers()`
3. Read `pick_delegation()`
4. Read `walk_from_root()`
5. Run `examples/dns/session_02_walkthrough.py`
6. Trace `www.example.com` by hand: which zone answers, and which zones only refer?

## Read It Like Code

```python
Zone(
    name,
    answers,
    delegations,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `name` | Where in the tree this zone sits. The root is the empty string. |
| `answers` | What this zone can answer directly, keyed by (name, type). |
| `delegations` | The child zones this zone can hand you off to. Referral, not answer. |

## Walk Loop

```text
start at root
  zone has (qname, qtype)?        -> answer, stop
  a delegation covers qname?      -> descend to the most specific child
  neither?                        -> dead end, stop
repeat, bounded by max_steps
```

## Reading Lens

The important move in this session is to stop thinking "the resolver asks DNS" and start asking:

- which zone was consulted at each step?
- did that zone answer, or did it refer?
- which condition ended the loop?

## Toy Model Boundary

Real iterative resolution sends packets to nameserver addresses and handles glue records. This lesson models each vantage point as a `Zone` object in a dict so the loop structure is readable without sockets.

`max_steps` plays the role that packet budgets and QNAME minimization limits play in real resolvers: the walk must be bounded.

## Code Landmarks

### `zone_covers()`

One suffix comparison. This is the entire meaning of "the name is inside this zone's subtree".

### `pick_delegation()`

When several children could cover the name, the longest match wins. The same "most specific wins" instinct you know from routing tables appears here.

### `walk_from_root()`

The main reading target. One loop, three exits: answer, no matching delegation, missing zone. The `path` list is the trace a debugging engineer wishes `dig +trace` output made this explicit.

## Failure Questions

Use the source file to answer these:

1. What does the walk return when a zone has no answer and no matching delegation?
2. What does `stopped_because` say when a delegation points to a zone nobody serves?
3. Why does the walk for `ftp.example.com` still reach `example.com` before failing?
4. What prevents the loop from running forever?
5. Why does the root zone cover every name?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dns/session_02_walkthrough.py
```

The walkthrough prints the zone path for each scenario, including a broken delegation.

## Done When

The learner can say all of the following without looking at notes:

- "Resolution is a loop that descends one delegation per iteration."
- "A zone either answers or refers. The walk only ends on an answer or a dead end."
- "The most specific delegation that covers the name is the one that gets followed."

## References

- RFC 1034 Section 4.3.2
- RFC 1034 Section 5.3.3
- RFC 8499 (zone, delegation, referral terminology)
