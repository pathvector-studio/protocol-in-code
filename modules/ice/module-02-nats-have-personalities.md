# Session 02 / Module 02: NATs Have Personalities

## Position

- Track: ICE
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/ice/module-02/index.html`
- Source file: `src/protocol_in_code/ice/nat_behavior.py`
- Walkthrough script: `examples/ice/session_02_walkthrough.py`

## Core Question

Given a set of observed mappings toward different destinations, what does the pattern of change (or lack of it) tell you about the NAT's personality?

## Outcome

By the end of this session, the learner should be able to:

- name the three `MappingBehavior` values, from most to least NAT-friendly for peer-to-peer
- explain what an `Observation` records and why both a destination and a mapping are required
- explain which check `classify_mapping()` runs first, and why the narrowest check must win
- explain why the toy NAT from the NAT track classifies as address-and-port-dependent, and what that costs a reflexive candidate

## Read Order

1. Read the module comment at the top of the file
2. Read `MappingBehavior`
3. Read `Observation`
4. Read `classify_mapping()`, including its docstring and the cross-reference to `nat/nat_loop.py`
5. Run `examples/ice/session_02_walkthrough.py`

## Read It Like Code

```python
Observation(
    dest_ip,
    dest_port,
    mapped_ip,
    mapped_port,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `dest_ip` / `dest_port` | Where the probe was sent. This is what varies across observations — the independent variable. |
| `mapped_ip` / `mapped_port` | What the NAT translated the sender into for that probe. This is what `classify_mapping()` watches for change. |

## Decision Flow

```text
mapping changes for the SAME dest_ip when only dest_port differs -> AddressAndPortDependent
mapping is stable per dest_ip, but differs ACROSS dest_ip values  -> AddressDependent
mapping never changes, regardless of dest_ip or dest_port         -> EndpointIndependent
```

## Reading Lens

This session follows directly from the NAT track. In `nat/module-01-a-connection-is-a-5-tuple.md` you read that the kernel tracks keys, not connections as a narrative — and in the NAT track's toy NAT box (`nat/nat_loop.py`, built out across `ports.py` and `table.py`) you built a NAT that allocates a fresh translated tuple per full 5-tuple. That box is not a neutral fact anymore; it has a personality, and this session gives you the vocabulary to name it.

The important move here is to stop asking "does this NAT work" and start asking:

- for a fixed `dest_ip`, does the mapping ever change when only `dest_port` changes?
- across different `dest_ip` values, does the mapping change at all?
- which of those two questions does `classify_mapping()` ask first, and why must it?

## Toy Model Boundary

Real NAT behavior discovery (as used by ICE agents and STUN-based NAT classification tools) requires actually probing multiple servers or multiple ports on one server and comparing live results, often across several round trips, and must handle mappings that expire between probes. This module skips the probing protocol entirely and hands `classify_mapping()` a fixed sequence of `Observation` values already collected — the classification logic is the whole story, not the mechanics of gathering evidence for it.

## Code Landmarks

### Module comment

States the source directly: RFC 4787 SS4.1 defines NAT personalities by what changes the mapping for the same internal `(ip, port)`. This module reads a sequence of observations and names the behavior they imply — it does not perform any probing itself.

### `MappingBehavior`

Three values, ordered in the docstring "from most to least NAT-friendly for peer-to-peer": `ENDPOINT_INDEPENDENT`, `ADDRESS_DEPENDENT`, `ADDRESS_AND_PORT_DEPENDENT`. The ordering is not incidental — it is the same order `classify_mapping()`'s checks run in, narrowest (strictest) first.

### `classify_mapping()`

The main reading target. It groups observed mappings by `dest_ip` into a `dict[str, set[tuple[str, int]]]`. The first check asks: for any single `dest_ip`, is there more than one distinct mapping in its set? If so, the mapping changed even when only the destination port varied — `ADDRESS_AND_PORT_DEPENDENT`, returned immediately, regardless of what the rest of the data shows. Only if every `dest_ip` maps to exactly one mapping does the function ask the second question: do those per-`dest_ip` mappings differ from each other? If so, `ADDRESS_DEPENDENT`. If nothing varied anywhere, `ENDPOINT_INDEPENDENT` — the fallback when no evidence of change exists.

The docstring's cross-reference is the payload of this session: `nat/nat_loop.py`'s `ToyNatBox` allocates one port per 5-tuple, so a new destination — even a different port on the same peer — gets a fresh translated tuple. The NAT you built in the NAT track IS address-and-port-dependent, the hardest personality for peer-to-peer, because a reflexive candidate learned from one STUN server predicts nothing about what a real peer will see.

## Failure Questions

Use the source file to answer these:

1. Which check does `classify_mapping()` run first — the one that can return `ADDRESS_AND_PORT_DEPENDENT`, or the one that can return `ADDRESS_DEPENDENT`? Why must the stricter check win even if the looser condition also holds?
2. Which pair of fields in two `Observation` values — held equal, and varied — is what separates an `AddressDependent` verdict from an `AddressAndPortDependent` one?
3. Given exactly one `Observation`, what does `classify_mapping()` return, and what does that tell you about what a single data point can prove?
4. Why does `classify_mapping()` build a `dict` keyed by `dest_ip` rather than checking all observations against each other directly?
5. Per the docstring's cross-reference, why is a reflexive candidate learned from a single STUN server worthless for predicting what a real peer will see, when the local NAT is address-and-port-dependent?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/ice/session_02_walkthrough.py
```

The walkthrough builds three observation sets that classify as endpoint-independent, address-dependent, and address-and-port-dependent in turn, checks what a single observation resolves to, and closes with the exact shape of mapping the toy NAT box from the NAT track would produce.

## Done When

The learner can say all of the following without looking at notes:

- "A NAT's personality is defined by what has to change before its mapping changes — nothing, the destination IP, or the destination IP and port both."
- "The strictest check runs first, because one address-and-port-dependent observation anywhere in the data overrides everything else."
- "The NAT I built in the NAT track allocates per full 5-tuple, which makes it address-and-port-dependent — the personality that breaks reflexive-candidate prediction entirely."

## References

- RFC 4787 (Network Address Translation (NAT) Behavioral Requirements for Unicast UDP), Section 4.1
