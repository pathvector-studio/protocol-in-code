# Session 08 / Module 08: Export Policy Decides What Leaves

## Position

- Track: BGP
- Session: 08
- Site lesson: `pathvector-site/courses/protocols-in-code/bgp/module-08/index.html`
- Source file: `src/protocol_in_code/bgp/export_policy.py`
- Walkthrough script: `examples/bgp/session_08_walkthrough.py`

## Core Question

Why is the route we advertise to a peer not always identical to the route we installed locally?

## Outcome

By the end of this session, the learner should be able to:

- explain why export policy is a separate step after local installation
- explain how `next-hop-self` changes outbound state
- explain how eBGP advertisement prepends the local AS in this toy model
- explain how a route can stay installed locally but still be denied on export

## Bridge From Previous Sessions

Session 06 introduced Adj-RIB-Out as a separate place where outbound state lives. Session 08 gives that outbound state its own policy function.

## Read Order

1. Read `PeerType`
2. Read `ExportPolicy`
3. Read `prepare_export()`
4. Notice the deny check
5. Notice `next_hop_self`
6. Notice how eBGP changes `as_path`
7. Run `examples/bgp/session_08_walkthrough.py`

## Read It Like Code

```python
if path.prefix in policy.deny_prefixes:
    return None

if policy.next_hop_self:
    exported = replace(exported, next_hop="self")

if peer_type is PeerType.EBGP:
    exported = replace(exported, as_path=((policy.local_as,) * prepend_count) + exported.as_path)
```

## Data That Matters

| Item | Why it matters |
|---|---|
| `deny_prefixes` | A route can stay in Loc-RIB and still not leave the router. |
| `next_hop_self` | Outbound state can differ from local state. |
| `peer_type` | eBGP and iBGP export do not look the same. |
| `extra_prepend_count` | Export policy can intentionally change path appearance. |

## Failure Questions

1. Which condition returns `None` on export?
2. When does `next_hop` become `"self"`?
3. When does the local AS get prepended?
4. Why is export policy not just "send Loc-RIB to everyone"?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/bgp/session_08_walkthrough.py
```

The walkthrough compares eBGP export, iBGP export with `next-hop-self`, and a deny case where the route remains local but is not advertised.

## Done When

The learner can say all of the following without looking at notes:

- "Installed route and exported route are different objects in practice."
- "Export policy can deny a prefix without deleting it from Loc-RIB."
- "`next-hop-self` rewrites outbound state."
- "eBGP export changes `as_path` in this toy model."
