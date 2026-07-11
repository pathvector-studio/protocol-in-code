# Session 04 / Module 04: Classes Form a Tree

## Position

- Track: QoS
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/qos/module-04/index.html`
- Source file: `src/protocol_in_code/qos/classes.py`
- Walkthrough script: `examples/qos/session_04_walkthrough.py`

## Core Question

Hierarchical shaping puts classes like "video" and "bulk" underneath "default" so they can share what "default" doesn't use — but a parent pointer alone doesn't make that sharing safe. What has to be true of the tree before any borrowing math is trustworthy, and how much can a class actually borrow on paper?

## Outcome

By the end of this session, the learner should be able to:

- name the three ways a class tree can be invalid, and which one `validate_tree()` catches first
- explain why cycle detection needs a `visited` set instead of just following `parent` until it's `None`
- compute over-subscription by hand: sum a parent's children's `guaranteed_rate` and compare to the parent's own
- compute `borrowable()` for a given class by hand, including the walk up through its ancestors
- state, without hedging, that `borrowable()` is a static tree-walk answer, not a live allocator

## Read Order

1. Read the module docstring at the top of `classes.py`
2. Read `TrafficClass` and `ClassTree`
3. Read `ValidationOutcome` and `ValidationResult`
4. Read `validate_tree()` top to bottom, one pass at a time
5. Read `borrowable()`
6. Run `examples/qos/session_04_walkthrough.py`

## Read It Like Code

```python
TrafficClass(
    name,
    guaranteed_rate,
    parent,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `name` | The key every other class's `parent` points at. There is no separate ID — the name is the identity. |
| `guaranteed_rate` | What this class is promised, and the ceiling its children's own promises must fit under. |
| `parent` | `None` at the root; otherwise another class's `name`. This single pointer is the entire tree structure — there is no explicit list of children anywhere. |

## Decision Flow

```text
validate_tree(tree):
  pass 1: every cls.parent (if not None) must be a key in tree.classes
            -> otherwise UNKNOWN_PARENT
  pass 2: for every class, walk cls -> parent -> parent -> ... tracking visited names
            -> a name seen twice before hitting None -> CYCLE
  pass 3: sum guaranteed_rate of each parent's direct children
            -> sum > parent.guaranteed_rate -> OVER_SUBSCRIBED
  otherwise -> VALID
```

## Reading Lens

The important move in this session is to stop reading `validate_tree()` as one function and start reading it as three independent passes over the same dict, each guarding a different failure mode:

- which pass would catch a given broken tree, and would an earlier pass catch it first?
- for `borrowable()`, at each step of the walk: whose `guaranteed_rate` is being read, and whose children's claims are being subtracted from it?
- is a number in `borrowable()`'s result describing bandwidth actually available right now, or bandwidth that exists only on paper in the tree's own arithmetic?

## Toy Model Boundary

`borrowable()` is deliberately the simplest honest rule: a class's borrowable capacity is its own unused guarantee (`guaranteed_rate` minus what its children already claim) plus the same computation walked up through every ancestor to the root. It does not model sibling contention, work-conserving redistribution, or bandwidth actually in flight — those require a live scheduler watching real traffic, not a static walk over a dict of dataclasses. This function answers exactly one question: "if this class needed more than its guarantee, how much slack does the chain above it have on paper, right now, with nothing else changing?" A production HTB-style shaper recomputes borrowing continuously as siblings' usage rises and falls; this toy computes it once, from the tree's shape alone.

`validate_tree()`'s cycle check walks each class's ancestor chain from scratch with a fresh `visited` set, which is O(n) per class — fine for a course-sized tree, not how a production validator would be written for a large config.

## Code Landmarks

### The module docstring's second paragraph

States the boundary before the code does. Read it before `borrowable()` so the function's simplicity reads as a choice, not an oversight.

### `validate_tree()`'s three separate loops

Three `for` loops over `tree.classes`, not one loop with three checks inlined. Each pass assumes the previous one already held — the cycle-detection pass, for instance, does `tree.classes[current]` without a membership check, trusting that pass one already confirmed every parent exists.

### The cycle-detection `while` loop

`visited: set[str] = set()` starts fresh for every class in the outer loop. The check is `if current in visited`, not `if current is cls.name` — a cycle two hops removed from the class currently being checked is still caught.

### `borrowable()`'s `children_sum` recomputation

`borrowable()` rebuilds the same `children_sum` dict that `validate_tree()`'s third pass builds — the two functions don't share it. Worth noticing as a small piece of duplicated work, and worth asking why the module doesn't factor it out.

## Failure Questions

Use the source file to answer these:

1. A class tree has exactly one class, `TrafficClass("solo", guaranteed_rate=10, parent="solo")` — its own name as its own parent. Pass one (`UNKNOWN_PARENT`) does not catch this, because `"solo"` is a key in `tree.classes`. Which `ValidationOutcome` does `validate_tree()` return instead, and on which pass?
2. Given the `good` tree in the walkthrough (`default=100` with children `video=60` and `bulk=30`), what does `borrowable(good, "default")` equal, and why does the walk stop after summing `default`'s own slack instead of continuing further?
3. `validate_tree()` runs its three passes in a fixed order: unknown-parent, then cycle, then over-subscription. Construct a tree that has both an unknown parent and an over-subscribed parent at the same time — which `ValidationOutcome` comes back, and why does the answer not depend on which failure mode you consider "worse"?
4. `borrowable()` never calls `validate_tree()` internally. If it is called on a tree that has a cycle, what actually happens when the `while current is not None` loop runs — does it terminate, and if not, what stops the program?
5. In `borrowable()`, the walk sums `max(cls.guaranteed_rate - used_by_children, 0)` at every ancestor, including the class asked about. Why does the walk floor each term at zero instead of letting it go negative for an already over-subscribed class?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/qos/session_04_walkthrough.py
```

The walkthrough validates a healthy two-level tree, then breaks it three separate ways — unknown parent, a two-node cycle, and an over-subscribed parent — before computing `borrowable()` for a leaf class and showing the arithmetic in the printed label.

## Done When

The learner can say all of the following without looking at notes:

- "A class tree is just a dict of dataclasses connected by a `parent` name — there is no separate tree data structure."
- "`validate_tree()` is three independent passes, each assuming the previous one already held."
- "`borrowable()` answers what the tree's shape allows on paper; it is not a live allocator and does not know about traffic actually in flight."

## References

- RFC 2475 (An Architecture for Differentiated Services) — the general DiffServ framing this class tree loosely echoes: traffic sorted into classes, each class getting a distinct forwarding treatment.
- This module's hierarchical borrowing is HTB-flavored (Hierarchical Token Bucket, as implemented in Linux `tc`), but the resemblance stops at the tree shape. Real HTB performs live borrowing — a class reaches up to a parent for spare bandwidth continuously, as actual queue occupancy changes — while `borrowable()` here is a one-shot static computation over `guaranteed_rate` fields with no queue, no scheduler, and no notion of current usage.
