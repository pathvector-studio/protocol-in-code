# Session 03 / Module 03: Ports Have Roles

## Position

- Track: STP
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/stp/module-03/index.html`
- Source file: `src/protocol_in_code/stp/port_roles.py`
- Walkthrough script: `examples/stp/session_03_walkthrough.py`

## Core Question

A bridge knows the root (Session 01) and can compare paths and BPDUs (Session 02, and `blocking.py`). What role does each of its own ports end up with, and how many of those roles can be "the way to root" at once?

## Outcome

By the end of this session, the learner should be able to:

- explain why every port on the root bridge is DESIGNATED, with no exceptions
- state the invariant `assign_roles()` asserts about ROOT_PORT and why exactly one, never zero or two
- explain what separates a DESIGNATED port from a BLOCKED port on a non-root bridge
- trace what happens to a port that has heard nothing at all

## Read Order

1. Read the module docstring at the top of the file
2. Read `PortRole`
3. Read `PortView`
4. Read `assign_roles()`
5. Read `blocking.Bpdu` and `blocking.should_block()` (Session 03 depends on them directly)
6. Run `examples/stp/session_03_walkthrough.py`

## Read It Like Code

```python
PortView(
    port_id,
    heard,
    my_offer,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `port_id` | Identity — which physical port this view describes. |
| `heard` | The best BPDU heard on this port so far, or `None` if nothing has been heard yet. Optional, and its absence changes the outcome. |
| `my_offer` | The BPDU this bridge would itself send on this port — its own claim to root, always present. |

## Decision Flow

```text
assign_roles(ports, i_am_root):
  i_am_root is True
    -> every port DESIGNATED

  i_am_root is False
    -> the port with the lowest my_offer.root_path_cost  -> ROOT_PORT (exactly one)
    -> every other port:
         heard is not None and should_block(heard, my_offer) -> BLOCKED
         otherwise                                            -> DESIGNATED
```

## Reading Lens

The important move in this session is to stop reading `assign_roles()` as three independent per-port checks and start asking:

- is this bridge the root at all? That one flag short-circuits everything else.
- of all my ports, which single one carries the cheapest offer — and what happens to the rest once that one is claimed?
- for a port that isn't the root port, what's being compared isn't "am I good enough in the abstract" — it's "does what I hear beat what I'd say," a direct call into Session 02's neighbor module (`blocking.should_block()`).

Notice what `assign_roles()` does *not* do: it never calls `path_cost.better_path()` directly. Its own docstring says the ROOT_PORT selection is "`best_path` picks it via `path_cost.better_path`'s ordering, here reduced to the cost each port's own offer already encodes" — the full three-stage tiebreak from Session 02 has already been folded into each port's `my_offer.root_path_cost` by the time this function runs. Reading `assign_roles()` well means recognizing what it's built on top of, not just what's written in its body.

## Toy Model Boundary

Real 802.1D distinguishes six port states (Blocking, Listening, Learning, Forwarding, Disabled, plus the RSTP-only Discarding) and moves a port through them over time, gated by hello and forward-delay timers, before it's trusted to forward traffic. This module collapses all of that into three static roles decided in one function call — ROOT_PORT, DESIGNATED, BLOCKED — computed from a snapshot of what's currently heard, with no timers, no aging, and no transition delay. This is classic STP's three-role vocabulary, not RSTP's (which adds Alternate and Backup port roles); per-VLAN spanning trees (PVST+, MST) are out of scope entirely — this module assumes one tree for the whole network.

## Code Landmarks

### The module docstring

States the shape up front: the root bridge is easy (every port DESIGNATED, "nothing can offer a better path to root than being the root"), every other bridge needs exactly one ROOT_PORT and, on every remaining port, either DESIGNATED or BLOCKED. Read this before the function body — it's the whole decision tree in three sentences.

### `assign_roles()` — the root branch

```python
if i_am_root:
    return {port.port_id: PortRole.DESIGNATED for port in ports}
```

One line, no per-port comparison at all. Being root isn't a special case of the general algorithm — it bypasses the general algorithm entirely.

### `assign_roles()` — choosing the ROOT_PORT

```python
root_port_id = min(ports, key=lambda port: port.my_offer.root_path_cost).port_id
```

A plain `min()` over `my_offer.root_path_cost`, echoing Session 01's `elect_root()` — same "reduce a comparison to one `min()` call" shape, different field being minimized.

### `assign_roles()` — the one-root-port invariant

```python
assert len(root_ports) == 1, "a non-root bridge must have exactly one root port"
```

This isn't a comment — it's an executable assertion at the end of the function. Every non-root call to `assign_roles()` re-verifies its own output before returning. If the input ever produced zero or two ROOT_PORTs, this line is where the bug would surface, loudly, rather than silently producing a broken role map.

### `blocking.should_block()`

`port_roles.py` imports `Bpdu` and `should_block` from `blocking.py` and calls `should_block(port.heard, port.my_offer)` directly — this session's DESIGNATED-vs-BLOCKED decision is not reimplemented here, it's delegated. `should_block()` in turn is `bpdu_is_superior(heard, mine)` — if what we hear beats what we'd say, we block; otherwise we speak.

## Failure Questions

Use the source file to answer these:

1. `assign_roles(ports, i_am_root=True)` is called. Does the function ever look at any port's `heard` or `my_offer.root_path_cost`? Which line makes that unreachable?
2. A non-root bridge has three ports. What line of `assign_roles()` guarantees exactly one of them becomes ROOT_PORT, and what would have to be true of the input for that guarantee to fail its own assertion?
3. A port's `heard` field is `None`. Walk the `elif`/`else` chain in `assign_roles()` — which branch does this port fall into, and why does `heard is not None` have to be checked before `should_block()` is ever called on it?
4. A port that is not the ROOT_PORT has `heard` set to a `Bpdu`. What function decides whether it's DESIGNATED or BLOCKED, and what is that function actually comparing under the hood (trace it into `blocking.py`)?
5. `assign_roles()`'s docstring says the ROOT_PORT selection is `path_cost.better_path`'s ordering "reduced to the cost each port's own offer already encodes." What does that imply about when the three-stage tiebreak from Session 02 actually ran, relative to when `assign_roles()` is called?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/stp/session_03_walkthrough.py
```

The walkthrough assigns roles for a root bridge (every port DESIGNATED), a non-root bridge with two ports (exactly one ROOT_PORT, asserted by count), a port hearing an offer that beats its own (BLOCKED), and a port that has heard nothing at all (DESIGNATED, per the `heard is not None` guard).

## Done When

The learner can say all of the following without looking at notes:

- "The root bridge never runs the general algorithm — every one of its ports is DESIGNATED by definition, in one line."
- "A non-root bridge always has exactly one ROOT_PORT, and the source asserts that invariant instead of just hoping for it."
- "A port that has heard nothing can't be BLOCKED — `should_block()` is never even called on it — so it defaults to DESIGNATED."

## References

- IEEE 802.1D (the standard defining port roles/states for STP; no RFC governs STP)
