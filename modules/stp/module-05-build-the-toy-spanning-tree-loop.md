# Session 05 / Module 05: Build the Toy Spanning Tree Loop

## Position

- Track: STP
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/stp/module-05/index.html`
- Source file: `src/protocol_in_code/stp/stp_loop.py`
- Walkthrough script: `examples/stp/session_05_walkthrough.py`

## Core Question

What does convergence actually look like when root election, path cost, and blocking are wired into a round-by-round exchange between real bridge objects instead of four separate demos?

## Outcome

By the end of this session, the learner should be able to:

- name every function `ToyStpBridge` calls and which earlier session's module owns it
- trace one round of `_exchange_round()`: emit, receive, recompute — in that order
- explain why `receive()` adds ingress cost before comparing, not after
- run the triangle to convergence and read off the root and the one blocked port from the trace
- explain why `fail_root()` on the triangle produces zero blocked ports, not a port "unblocking"

## Read Order

1. Read the module docstring in full
2. Read `ToyStpBridge`'s field list
3. Read `cost_to_root()` and `root_port_id()`
4. Read `emit_bpdus()`
5. Read `receive()`
6. Read `recompute_blocked()`
7. Read `_exchange_round()` and `converge()`
8. Read `triangle()`
9. Read `fail_root()`
10. Run `examples/stp/session_05_walkthrough.py`

## Read It Like Code

```python
ToyStpBridge(
    bridge_id,
    ports,
    best_bpdu_heard,
    trace,
    blocked_ports,
)
```

## Parts List

Every function `stp_loop.py` imports was taught by an earlier session in this track. The capstone's only new code is the round-by-round wiring between them.

| Import | Session that taught it | What it contributes to `ToyStpBridge` |
|---|---|---|
| `root_election.BridgeId`, `elect_root` | 01 | `bridge_id`; `converge()` calls `elect_root()` once, up front, to fix `root` for every round that follows. |
| `path_cost.PORT_COST` | 02 | `DEFAULT_SPEED_MBPS = 100` resolves to `PORT_COST[100] == 19`, the ingress cost `receive()` charges on every hop. |
| `blocking.Bpdu`, `bpdu_is_superior` | 04 | `best_bpdu_heard`'s value type, and the exact comparison `receive()` and `recompute_blocked()` both call to decide what's kept and what's blocked. |
| *(not imported directly)* `port_roles.py` | 03 | Not used here — `recompute_blocked()` re-derives blocking on its own terms (root port vs. everything else), rather than calling `assign_roles()`. The capstone's blocking logic and Session 03's role-assignment logic are two independent readings of the same underlying comparison. |

`port_roles.py` is listed to make its absence explicit: this capstone does not produce `PortRole.ROOT_PORT` / `DESIGNATED` / `BLOCKED` labels, only a `blocked_ports: set[int]`. Session 03 and this module both start from `bpdu_is_superior()`, but they answer different questions — one assigns a role per port, the other only decides block-or-not.

## Decision Flow

```text
converge(bridges, segments, rounds):
  root = elect_root(all bridge_ids)                    # Session 01
  repeat up to `rounds` times:
    _exchange_round(bridges, segments, root):
      1. every bridge.emit_bpdus(root)                 -> one Bpdu per non-blocked port
      2. for each segment, every OTHER member receives  -> bridge.receive(port_id, bpdu)
           receive(): arrived.root_path_cost = bpdu.root_path_cost + PORT_COST[100]   # Session 02
                       keep it only if bpdu_is_superior(arrived, current)             # Session 04
                       kept -> trace.append(...)
      3. every bridge.recompute_blocked(root)
           root bridge          -> blocked_ports = {} (nothing to defer to)
           non-root, per port:
             port is root_port_id(root) -> never blocked
             else: bpdu_is_superior(heard, my_offer) -> blocked
    if nothing changed this round -> stop, report rounds_run = this round
  if `rounds` exhausted without stabilizing -> report rounds_run = rounds
```

## Reading Lens

The important move in this session is to stop reading `blocking.py` and `path_cost.py` as standalone comparisons and start asking, at every call in `_exchange_round()`:

- whose cost is this — the cost as emitted, or the cost as it arrived after `receive()` added a hop?
- did `best_bpdu_heard` for this port actually change this round, or did the incoming BPDU lose the comparison and get discarded silently?
- is `_exchange_round()` returning `True` because something changed, or is convergence just the round where nothing did?

## Toy Model Boundary

Real STP exchanges BPDUs continuously — every bridge re-sends its best BPDU roughly every 2 seconds (the hello time), and ports move through Listening and Learning states with a forward delay timer before a newly-unblocked port is trusted to carry traffic. This module has none of that: `converge()` runs synchronous rounds, one full emit-receive-recompute cycle per call, until nobody's `best_bpdu_heard` changes — there is no clock, no hello timer, and no transitional port state between BLOCKED and forwarding. There are also no topology-change notifications; `fail_root()` does not simulate a bridge going silent and timing out, it removes the bridge and its segment memberships outright, then re-converges from a clean slate (`best_bpdu_heard` and `blocked_ports` are both reset on every surviving bridge before the new round-robin starts). Real STP's reconvergence after a root failure can take tens of seconds precisely because of the timers this toy skips.

## Code Landmarks

### The module docstring's "spare tire" framing

Sets up the payoff before you read a line of code: the triangle converges with exactly one blocked port, and that port is not dead weight — it is provisioned capacity, ready the moment `fail_root()` changes the topology. Read this before `triangle()`.

### `receive()`'s cost arithmetic

`arrived = Bpdu(..., root_path_cost=bpdu.root_path_cost + PORT_COST[DEFAULT_SPEED_MBPS], ...)`. The addition happens before the `bpdu_is_superior()` comparison, not after — this is `path_cost.accumulate()`'s rule (cost is charged on the receiving port) inlined directly into the bridge's own receive path.

### `recompute_blocked()`'s root-port exemption

`if port_id == root_port: continue`. A bridge's root port is never blocked, no matter what it hears there — it is definitionally the port carrying the best path to root, so there is nothing for it to lose a comparison against.

### `fail_root()`'s reset-before-reconverge

`bridge.best_bpdu_heard = {}` and `bridge.blocked_ports = set()` on every surviving bridge, before `converge()` runs again. Nothing carries over from the old topology; the new convergence is computed from scratch, the same way `triangle()`'s first convergence was.

## Failure Questions

Use the source file to answer these:

1. `receive()` adds `PORT_COST[DEFAULT_SPEED_MBPS]` to `bpdu.root_path_cost` before ever comparing. What would change about `recompute_blocked()`'s outcome on the triangle if that addition were skipped?
2. `recompute_blocked()` consults `root_port_id(root)` before deciding anything else. What does `root_port_id()` return, and from which of the bridge's own fields does it compute that answer?
3. In the triangle, `emit_bpdus()` is called on every bridge every round, including on already-blocked ports the round after blocking is first computed. Read `emit_bpdus()` — does a blocked port ever appear in its returned dict? What enforces that?
4. `converge()` reports `rounds_run` as whichever round number `_exchange_round()` first returns `False` on. If `_exchange_round()` returned `True` on every one of the `rounds` calls, what would `rounds_run` equal, and would that mean the network failed to converge?
5. `fail_root()` filters `surviving_segments` to only those with `len(members) >= 2`. Which segment in the triangle drops out entirely once bridge `A` is removed, and why does a segment with fewer than two members need to be dropped rather than kept with one member?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/stp/session_05_walkthrough.py
```

The walkthrough builds the triangle, converges it, and checks that convergence takes exactly 2 rounds, that the unanimous root is bridge A's `BridgeId`, and that exactly one port is blocked — `('C', 2)`. It then checks C's own `trace` for the specific line recording what C heard on port 2 (A's BPDU, cost 19) — the BPDU that `recompute_blocked()` compares C's own offer against to produce the block. Finally it fails the root with `fail_root()` and checks that the new root is B and that `blocked_ports` comes back empty: removing A did not free up a spare port, it removed the loop the blocked port existed to break.

## Done When

The learner can say all of the following without looking at notes:

- "Every function stp_loop.py calls — elect_root, PORT_COST, bpdu_is_superior — was taught in an earlier session; this module only wires them into a round-by-round loop."
- "receive() charges the ingress cost before comparing, because cost accumulates on the receiving port, not the sending one."
- "The triangle converges with exactly one blocked port, C's port to A, because that's the one segment where a bridge's own re-advertisement collided with the root speaking for itself."
- "Failing the root in a three-bridge triangle doesn't unblock a spare port — it removes the loop, so recompute_blocked() finds nothing left to block."

## References

- IEEE 802.1D (no RFC governs the Spanning Tree Protocol; it is defined entirely in the IEEE 802.1D standard)
