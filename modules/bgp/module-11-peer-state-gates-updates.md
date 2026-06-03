# Session 11: Peer State Gates UPDATE

## Question

What has to be true before the control plane should accept an UPDATE from a neighbor?

## Source

- `src/protocol_in_code/bgp/peer_state.py`
- Companion source: `src/protocol_in_code/bgp/session.py`

## Read Order

1. Open `open_peer_session()` and confirm that it simply wraps `establish_neighbor()`.
2. Read `session_accepts_updates()` and notice that the gate is one boolean question: is this peer in `Established`?
3. Read `receive_update_if_established()` and confirm that the whole write into `Adj-RIB-In` is conditional on that gate.

## Why This Session Exists

Session 10 showed an integrated pipeline, but it quietly assumed that the incoming route had already passed the session gate.
This session makes that gate explicit.

## Code Lens

```python
def receive_update_if_established(adj_rib_in, peer, prefix, attributes):
    if not session_accepts_updates(peer):
        return False

    store_received_path(adj_rib_in, peer.peer_id, prefix, attributes)
    return True
```

The important thing is not the amount of code.
It is the placement of the `if`.

## Toy Model Boundary

This lesson isolates only the session-state gate.
It does not model address-family activation or negotiated capability checks, so `Established` should be read here as the first gate in the toy model, not the only gate a real implementation might use.

## Walkthrough

Run:

```bash
PYTHONPATH=src python3 examples/bgp/session_11_walkthrough.py
```

Look for:

- one peer whose TCP reachability never gets it to `Established`
- one peer whose UPDATE is accepted
- only the established peer appearing in `Adj-RIB-In`

## Done When

- You can explain why `Established` is not just a status label but a write permission.
- You can point to the exact `if` that keeps a route out of `Adj-RIB-In`.
