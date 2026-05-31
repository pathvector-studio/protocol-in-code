# Session 02 / Module 02: How UPDATE Changes State

## Position

- Track: BGP
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/bgp/module-02/index.html`
- Source file: `src/protocol_in_code/bgp/update.py`
- Walkthrough script: `examples/bgp/session_02_walkthrough.py`

## Core Question

How does a BGP UPDATE change routing state, and why is route withdrawal different from session failure?

## Outcome

By the end of this session, the learner should be able to:

- explain the difference between `NLRI` and `Withdrawn Routes`
- explain why announcement and withdrawal are different mutations
- explain why a route disappearing is not the same thing as a session dying
- explain why path attributes travel with an advertised route

## Read Order

1. Read `PathAttributes`
2. Read `BGPUpdate`
3. Read `RoutingTable.apply_update()`
4. Read `RoutingTable.withdraw()`
5. Read `apply_update_message()`
6. Run `examples/bgp/session_02_walkthrough.py`
7. Explain each table mutation in your own words

## Read It Like Code

```python
apply_update_message(table, update)
```

Inside that message, there are two different kinds of work:

```python
table.withdraw(prefix)
table.apply_update(prefix, path_attributes)
```

## Data That Matters

| Item | Why it matters |
|---|---|
| `withdrawn_routes` | Tells you which prefixes should disappear from the table. |
| `nlri` | Tells you which prefixes are being announced. |
| `path_attributes` | Carries the policy and path context for the announcement. |
| `paths_by_prefix` | Holds the current routing state after each mutation. |

## Reading Lens

The important move in this session is to stop thinking of UPDATE as "a packet to decode" and start asking:

- what disappeared?
- what appeared?
- which attributes arrived with the new path?
- did the route leave because of a withdrawal, or because the session itself died?

## Code Landmarks

### `PathAttributes`

This tells you what arrives with an announced route.

### `BGPUpdate`

This tells you what the incoming message can contain.

### `RoutingTable`

This is the state container that changes.

### `apply_update_message()`

This is the main reading target for Session 02.

It answers:

- why withdrawals are handled first
- why announcements need attributes
- how one UPDATE can both remove and add routes

## Failure Questions

Use the source file to answer these:

1. What happens if `withdrawn_routes` contains a prefix that already exists?
2. What happens if `path_attributes` is `None`?
3. What happens if the UPDATE contains only withdrawals?
4. What happens if the UPDATE contains both withdrawals and NLRI?
5. Why is this different from clearing the whole table because a session died?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/bgp/session_02_walkthrough.py
```

The walkthrough prints a sequence of updates and shows how the routing table changes after each one.

## Done When

The learner can say all of the following without looking at notes:

- "A withdrawal removes a prefix from the table, but does not by itself mean the BGP session is down."
- "An announcement needs both prefix data and path attributes."
- "One UPDATE can contain both removal work and addition work."

## References

- RFC 4271 Section 3.1
- RFC 4271 Section 4.3
- RFC 4271 Section 5
