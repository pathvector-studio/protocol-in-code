# Session 03 / Module 03: Snooping Reads Someone Else's Mail

## Position

- Track: IGMP
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/igmp/module-03/index.html`
- Source file: `src/protocol_in_code/igmp/snooping.py`
- Walkthrough script: `examples/igmp/session_03_walkthrough.py`

## Core Question

IGMP is a layer-3 conversation between hosts and routers — a switch was never addressed by it. So how does a switch prune multicast traffic without breaking the layering it has no business crossing?

## Outcome

By the end of this session, the learner should be able to:

- explain why a switch with no snooping has exactly one honest option for multicast: flood
- state what evidence `forward_ports()` requires before it narrows delivery to a group
- explain why the querier port is always in the forwarding set, even with zero observed reports there
- name the layering violation this module commits, and why it commits it anyway

## Read Order

1. Read the module comment at the top of the file
2. Read `SnoopingTable`
3. Read `observe_report()`
4. Read `observe_query()`
5. Read `forward_ports()`
6. Read `unknown_group_behavior()`
7. Run `examples/igmp/session_03_walkthrough.py`

## Read It Like Code

```python
SnoopingTable(
    port_groups,
    querier_port,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `port_groups` | `dict[int, set[str]]` — per switch port, the multicast groups a report was overheard requesting there. This is the switch's own, lesser copy of what `membership.py` already models correctly at the router. |
| `querier_port` | The one port a query was ever overheard on. `None` until `observe_query()` runs at least once. |

## Decision Flow

```text
forward_ports(group, all_ports):
  for each port in all_ports:
    group in port_groups.get(port, set())   -> included (a member reported here)
    port == querier_port                    -> included (the router's port, always)
    otherwise                                -> excluded

unknown_group_behavior(all_ports):
  no evidence at all for this group  -> every port (flood — the same as no snooping)
```

## Reading Lens

The important move in this session is to stop asking "what does the switch know" and start asking "what is the switch allowed to assume from silence." Ask, at every line:

- is this port included because of positive evidence (`observe_report()` ran for it), or because it's the querier port?
- if a group has never been reported on any port, does `forward_ports()` even get a chance to prune it, or does something else take over first?
- what would this switch do differently from a switch that never parsed a single IGMP packet?

## Toy Model Boundary

There is one switch and one querier port in this module — no querier election, no multiple routers on the same segment, and no handling for what happens if the querier itself changes mid-session. `port_groups` is built purely from `observe_report()`; there is no separate aging or expiry inside `snooping.py` itself — Session 04's `ToySnoopingSwitch.prune()` is what removes a port from a group, and it does so only by mirroring an expiry the querier already decided, never independently. There is no IGMPv3 source-specific forwarding here either — a port is either "wants this group" or it isn't, with no per-source narrowing.

## Code Landmarks

### The module comment at the top of the file

States the thesis outright: "IGMP snooping is a deliberate layering violation." The alternative it names — flood every port, because a switch with no layer-3 concept of "who wants this" has no other honest option — is the whole reason this module exists. Read this before the first function.

### `observe_report()`

`table.port_groups.setdefault(port, set()).add(group)` — the switch's only source of truth. Nothing else in this module ever adds a group to a port.

### `observe_query()`

One line, `table.querier_port = port`, but the docstring is the landmark: "A query can only have come from a router — that's where the querier lives." The switch identifies the router not by any special marker, but purely by the direction one specific message type came from.

### `forward_ports()`

The `or` in the generator expression is the entire pruning logic: `group in table.port_groups.get(port, set()) or port == table.querier_port`. The docstring explains why the querier port is unconditional — the router may have downstream members the switch can't see, and it needs the traffic regardless to route it onward.

### `unknown_group_behavior()`

One line, `return all_ports`. The docstring's framing is the landmark: "Silence is not evidence of absence." This function exists to make the honest fallback a named, deliberate function rather than an implicit default buried inside `forward_ports()`.

## Failure Questions

Use the source file to answer these:

1. `forward_ports()` is called for a group with zero entries in `port_groups` anywhere, but `querier_port` is set. What tuple comes back, and which single condition in the generator expression is responsible?
2. Why is the querier port included in `forward_ports()`'s result unconditionally, rather than only when a report happens to have been observed there too?
3. `observe_report()` is called for a port that has never been seen before. Does it raise, or does it create an entry? Which method call makes that guarantee?
4. What is the exact difference in behavior between `forward_ports()` for a group with no evidence anywhere and `unknown_group_behavior()` — do they produce different results, or the same one, for that case?
5. Nothing in `snooping.py` ever calls anything in `membership.py`. What does that tell you about whether the switch's `port_groups` and the router's `GroupTable` are the same object, or two independent, possibly-inconsistent copies of similar information?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/igmp/session_03_walkthrough.py
```

The walkthrough overhears a query on port 0, overhears reports on two other ports, prunes forwarding to member ports plus the querier port only, floods an unknown group across all ports, and confirms the querier port is present in both the pruned and the flooded results.

## Done When

The learner can say all of the following without looking at notes:

- "A switch with no snooping has exactly one honest behavior for multicast: flood every port — that's what `unknown_group_behavior()` deliberately preserves."
- "`forward_ports()` narrows delivery to member ports plus the querier port — never to members alone."
- "Snooping is a layering violation the switch commits on purpose, eavesdropping on traffic never addressed to it, purely so it can prune instead of flood."

## References

- RFC 4541 (informational — considerations for IGMP/MLD snooping switches; this module follows its member-ports-plus-router-ports shape but is not a conformance implementation)
