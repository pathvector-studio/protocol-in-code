# Session 15: Build The Toy Speaker Loop

## Question

What does the smallest readable BGP speaker look like when all previous sessions are connected?

## Source

- `src/protocol_in_code/bgp/speaker.py`

## Read Order

1. Read `ToyBGPSpeaker` as a bag of state: peers, export targets, `Adj-RIB-In`, `Loc-RIB`, `Adj-RIB-Out`, VRPs, and policies.
2. Read `_step_from_event()` and see how event results become the speaker API.
3. Read `receive_announce()`, `receive_withdraw()`, and `peer_down()` in that order.
4. Confirm that each method delegates to the Session 13 event functions.

## Bridge From Previous Sessions

- Session 11 gave us the session gate.
- Session 12 gave us export refresh.
- Session 13 gave us event-specific branches.
- Session 14 gave us prefix-wide policy-aware best-path.
- This session puts them into one speaker-shaped object by wrapping those event branches as methods.

## Code Lens

```python
result = process_announce_event(...)
return self._step_from_event("announce", result)
```

That three-step rhythm is the course in miniature.

## Walkthrough

Run:

```bash
PYTHONPATH=src python3 examples/bgp/session_15_walkthrough.py
```

Look for:

- first announce installing one path
- second announce keeping or changing the best path
- withdraw moving the prefix to the remaining peer
- peer-down removing the last remaining path and downgrading the peer state
- outbound advertisements changing as the speaker state changes

## Simplification Note

This is still a teaching model.
It does not implement timers, packet parsing, capability negotiation, or UPDATE encoding.
It shows the control-plane loop shape, not a production speaker.

## Done When

- You can explain the speaker as one object with state plus three event handlers.
- You can see how Sessions 01-14 collapse into a single readable control-plane loop.
