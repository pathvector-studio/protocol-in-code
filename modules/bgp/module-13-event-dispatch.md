# Session 13: Event Dispatches Announce, Withdraw, and Peer Down

## Question

What function decides which control-plane path to run for announce, withdraw, and peer-down events?

## Source

- `src/protocol_in_code/bgp/events.py`

## Read Order

1. Read `AnnounceEvent`, `WithdrawEvent`, and `PeerDownEvent` as separate triggers.
2. Read `process_announce_event()` and note the order: gate the peer, recompute best path, refresh exports.
3. Read `process_withdraw_event()` and see that it skips peer gating and starts by removing state.
4. Read `process_peer_down_event()` and notice that one peer-down can touch multiple prefixes.

## Bridge From Previous Sessions

- Session 11 made the session gate explicit.
- Session 12 made export refresh explicit.
- This session shows how those parts are chosen by event type.
- Session 14 will deepen the prefix-level decision logic, but the dispatch shape introduced here remains the same.

## Code Lens

```python
if announce:
    gate peer
    recompute prefix
    refresh exports
elif withdraw:
    remove received path
    recompute prefix
    refresh exports
elif peer_down:
    remove whole peer table
    recompute affected prefixes
    refresh exports
```

The exact code is longer, but the shape above is the point.

## Walkthrough

Run:

```bash
PYTHONPATH=src python3 examples/bgp/session_13_walkthrough.py
```

Look for:

- one announce producing a best path
- one withdraw removing that best path
- one second announce restoring it
- one peer-down withdrawing all affected exports

## Design Choice

This event layer keeps the branches small by delegating prefix-level decision work to helpers.
The point of the lesson is the event split itself: announce, withdraw, and peer-down do not enter the control plane the same way.

## Done When

- You can explain why `announce`, `withdraw`, and `peer down` are different branches instead of one generic update function.
- You can say which branch touches one prefix and which branch can touch many.
