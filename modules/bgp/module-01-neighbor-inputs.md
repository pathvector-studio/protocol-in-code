# Session 01 / Module 01: What a BGP Neighbor Needs

## Position

- Track: BGP
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/bgp/module-01/index.html`
- Source file: `src/protocol_in_code/bgp/session.py`
- Walkthrough script: `examples/bgp/session_01_walkthrough.py`

## Core Question

What inputs are required to form a BGP neighbor, and where does the session stop when one of them is missing?

## Outcome

By the end of this session, the learner should be able to:

- list the minimum inputs needed for a BGP session
- explain why `peer_ip` alone is not enough
- distinguish TCP failure from OPEN failure
- explain why `Established` is a state transition result, not just a config line

## Read Order

1. Read `BGPSessionConfig`
2. Read `SessionState`
3. Read `establish_neighbor()`
4. Run `examples/bgp/session_01_walkthrough.py`
5. Explain each early return in your own words

## Read It Like Code

```python
BGPSessionConfig(
    peer_ip,
    peer_as,
    local_as,
    tcp_reachable,
    hold_time,
    keepalive_time,
    capabilities,
    open_message_ok,
    keepalive_received,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `peer_ip` | Without a destination, TCP cannot start. |
| `peer_as` | You need a remote identity to validate the session. |
| `local_as` | You need a local identity to speak in the OPEN message. |
| `tcp_reachable` | BGP depends on TCP before any BGP message exchange happens. |
| `hold_time` / `keepalive_time` | The session is not only created, but maintained under timer rules. |
| `capabilities` | The peers need to agree on what they can talk about. |
| `open_message_ok` | OPEN negotiation can fail even when TCP is fine. |
| `keepalive_received` | The session is not fully established until KEEPALIVE succeeds. |

## State Machine

```text
Idle -> Connect -> Active -> OpenSent -> OpenConfirm -> Established
```

## Reading Lens

The important move in this session is to stop thinking in terms of "did the config look correct?" and start asking:

- which field was missing?
- which condition failed?
- which state was the last successful one?

## Code Landmarks

### `BGPSessionConfig`

The dataclass tells you what inputs exist.

### `SessionState`

The enum tells you what named states the code cares about.

### `establish_neighbor()`

This is the main reading target for Session 01.

It answers:

- where do we leave `Idle`?
- when do we fall back to `Active`?
- what must be true before `OpenSent` can move forward?
- why does `Established` happen last?

## Failure Questions

Use the source file to answer these:

1. What state do we return if `peer_ip` is empty?
2. What state do we return if TCP is not reachable?
3. What state do we return if the AS values are invalid?
4. What state do we return if OPEN negotiation fails?
5. What state do we return if KEEPALIVE never arrives?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/bgp/session_01_walkthrough.py
```

The walkthrough prints several scenarios and shows which state each one reaches.

## Done When

The learner can say all of the following without looking at notes:

- "BGP does not start at OPEN. It starts after TCP reachability."
- "OPEN failure and TCP failure stop in different places."
- "`Established` is the result of passing several checks, not a single setting."

## References

- RFC 4271 Section 1.1
- RFC 4271 Section 3
- RFC 4271 Section 4.2
