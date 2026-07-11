# Session 01 / Module 01: Group Membership Is a Set

## Position

- Track: IGMP
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/igmp/module-01/index.html`
- Source file: `src/protocol_in_code/igmp/membership.py`
- Walkthrough script: `examples/igmp/session_01_walkthrough.py`

## Core Question

What is a multicast group, really — and why does the whole membership picture collapse to ordinary set operations?

## Outcome

By the end of this session, the learner should be able to:

- explain why `GroupTable` is a `dict[str, set[str]]` and nothing fancier
- state which address range makes a group address valid, and where that check lives
- trace what `join()` and `leave()` do to the underlying dict, including the empty-set case
- explain why `anyone_interested()` is the one question multicast forwarding needs answered

## Read Order

1. Read `MULTICAST_RANGE` and `JoinOutcome`
2. Read `GroupTable`
3. Read `is_multicast_group()`
4. Read `join()`
5. Read `leave()`
6. Read `anyone_interested()`
7. Read `groups_of()`
8. Run `examples/igmp/session_01_walkthrough.py`

## Read It Like Code

```python
GroupTable(
    groups,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `groups` | `dict[str, set[str]]` — a multicast group address mapped to the set of hosts currently in it. There is no other state. |

## Decision Flow

```text
join(group, host):
  group not in 224.0.0.0/4    -> MalformedGroup (no set touched)
  host already in members     -> AlreadyMember   (set unchanged)
  otherwise                   -> JOINED           (host added to the set)

leave(group, host):
  group not in table          -> no-op
  host removed from members
  members now empty           -> the group key itself is deleted
```

## Reading Lens

The important move in this session is to stop picturing "a multicast group" as a router-side concept and start reading it as exactly what the code says it is: a set of hosts, keyed by address, that either exists or doesn't. Ask, at every line:

- is this line touching the set's membership, or just answering a question about it?
- after this call, does the key `group` still exist in `table.groups` at all?
- would `anyone_interested()` change its answer because of this line?

## Toy Model Boundary

This module models IGMPv2-style any-source membership only — there is no source filtering (`INCLUDE`/`EXCLUDE` mode, source lists) the way IGMPv3 defines it. A host is a bare name string, not an IP address with its own validity rules. There is no message on the wire here at all — `join()` and `leave()` are called directly, as if a report had already been parsed; Session 02 and Session 04 are where a query cycle actually drives these calls over time.

## Code Landmarks

### `MULTICAST_RANGE`

`ip_network("224.0.0.0/4")`, computed once at import time. Every address check in this file traces back to this one constant.

### `is_multicast_group()`

The only validity check `join()` runs. It catches `ValueError` from `ip_address()` too, so a string that isn't even a valid IP address returns `False` rather than raising.

### `join()`

`table.groups.setdefault(group, set())` is the whole mechanism: the group key is created on first join, on demand, with no separate "create group" step anywhere in this module.

### `leave()`

The landmark line is `if not members: del table.groups[group]`. The docstring calls a leftover empty set "a lie" — read that line before anything else in this function.

### `anyone_interested()`

One line: `bool(table.groups.get(group))`. Because `leave()` deletes empty sets, this never has to distinguish "key missing" from "key present but empty" — both are falsy the same way.

## Failure Questions

Use the source file to answer these:

1. `leave()` is called for the last member of a group. What happens to the key `group` inside `table.groups` — does it stay as an empty set, or is it removed? Which line does that?
2. Why does `anyone_interested()` not need to check `group in table.groups` separately from checking whether the set is non-empty?
3. `join(table, "10.0.0.5", "host-a")` is called. What `JoinOutcome` comes back, and does `table.groups` change at all?
4. `join()` is called twice in a row for the same group and host. What is the `JoinOutcome` the second time, and what changed in the underlying set between the two calls?
5. `groups_of()` returns a sorted tuple rather than the dict's natural iteration order. What would a caller relying on insertion order get wrong if `groups_of()` didn't sort?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/igmp/session_01_walkthrough.py
```

The walkthrough joins a host, joins it again, tries a unicast address, drives a group's last member out through `leave()` and asserts the key is gone, and reads `groups_of()` for a host in two groups.

## Done When

The learner can say all of the following without looking at notes:

- "A multicast group is nothing but its current member set — the dict key exists exactly when the set is non-empty."
- "`join()` and `leave()` are set insertion and set removal, plus one address-range check on the way in."
- "`anyone_interested()` is the one question multicast forwarding actually needs answered, and it's a single dict lookup."

## References

- RFC 2236 Section 1 (Introduction — group membership as a set of interested hosts)
- RFC 2236 Section 2 (the 224.0.0.0/4 address range this module validates against)
