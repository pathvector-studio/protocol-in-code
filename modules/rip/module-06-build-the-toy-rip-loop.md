# Session 06 / Module 06: Build the Toy RIP Loop

## Position

- Track: RIP
- Session: 06
- Site lesson: `pathvector-site/courses/protocols-in-code/rip/module-06/index.html`
- Source file: `src/protocol_in_code/rip/speaker.py`
- Walkthrough script: `examples/rip/session_06_walkthrough.py`

## Core Question

What does the smallest readable RIP speaker look like when a routing table, a neighbor list, an outbound filter, and a Bellman-Ford pass are all wired into one object that a round-robin exchange loop can drive to convergence — and how is that whole shape different from OSPF's?

## Outcome

By the end of this session, the learner should be able to:

- name every field on `ToyRipSpeaker` and which earlier session's module owns the behavior it wires in
- trace one full `converge()` run by hand for a small chain and predict the round count
- explain why `lose_connected()` poisons a route instead of deleting it
- state, in one sentence each, how RIP's speaker loop and OSPF's speaker loop solve the same problem by opposite means

## Read Order

1. Read the module docstring in `speaker.py`, including its closing paragraph about OSPF
2. Read `ToyRipSpeaker`'s field list top to bottom
3. Read `__post_init__()`
4. Read `advertise_to()`
5. Read `receive()`
6. Read `lose_connected()`
7. Read `ConvergenceReport`
8. Read `converge()`
9. Run `examples/rip/session_06_walkthrough.py`

## Read It Like Code

```python
ToyRipSpeaker(
    name,
    table,
    connected,
    neighbors,
    trace,
)
```

## Parts List

Every field and every function `speaker.py` imports was taught by an earlier session in this track. The capstone's only new code is the exchange loop that drives them together.

| Import | Session that taught it | What it contributes to `ToyRipSpeaker` |
|---|---|---|
| `route.RipRoute` | 01 | The record type every table entry is made of — `prefix`, `metric`, `next_hop`, `learned_from`. |
| `update.RoutingTable`, `UpdateOutcome`, `process_advertisement` | 02-03 | `table`; `process_advertisement()` is the Bellman-Ford pass `receive()` delegates to on every inbound advertisement. |
| `count_to_infinity.py` (no direct import — the failure mode this speaker is built to avoid) | 04 | The motivating problem: an unfiltered version of this same exchange loop is exactly what climbs to `INFINITY`. |
| `split_horizon.advertisable` | 05 | `advertise_to()`'s entire body — every outbound advertisement is filtered through this before a neighbor ever sees it. |
| `infinity.poison` | 04-05 (defined earlier, in `infinity.py`) | `lose_connected()`'s repair action — marks a lost route as unreachable in place instead of deleting the table entry. |

Session 04's `count_to_infinity.py` is listed without a direct import because it is the demonstration this capstone is structurally guarding against: `advertise_to()` calling `advertisable()` on every round is the fix from Session 05 wired permanently into the speaker, so the failure from Session 04 cannot happen inside `converge()`.

## Decision Flow

```text
converge(speakers, rounds):
  for round_no in 1..rounds:
    # advertise phase: every speaker computes what it would send to every
    # neighbor, filtered through split horizon, before anyone receives anything
    for each speaker, for each of its neighbors:
      outgoing[(speaker, neighbor)] = speaker.advertise_to(neighbor)

    # receive phase: every outgoing advertisement is folded into the
    # receiver's table via Bellman-Ford; track whether anything changed
    changed = False
    for each (sender, receiver) in outgoing:
      before = snapshot of receiver's table
      receiver.receive(sender, outgoing[(sender, receiver)])
      if receiver's table != before: changed = True

    changed == False  -> stop, report converged=True, rounds_run=round_no
    changed == True    -> next round

  loop exhausts `rounds` without stabilizing -> report converged=False, rounds_run=rounds
```

## Reading Lens

The important move in this session is to stop reading `advertise_to()` and `receive()` as two independent methods and start asking, at every round of `converge()`:

- is this round's advertise phase using tables from *before* any receive phase ran this round, or could a speaker see a neighbor's already-updated table mid-round? (Read `converge()` closely — it computes every `outgoing` advertisement before any `receive()` call happens.)
- which single field decided whether `advertise_to()` includes or omits a given route — the same field Session 05 taught you to check?
- what does `changed` mean operationally: is it "did any metric change" or "did the routes dict compare unequal" — and does that distinction matter?

The link-state contrast: `ospf/speaker.py`'s capstone builds a speaker whose job is to flood an unchanged fact (a Router-LSA) and let every router recompute shortest paths locally from a shared map via Dijkstra (`ospf/spf.py`). This module's speaker never floods anything unchanged and never builds a map — `receive()` takes one neighbor's numbers, adds one, and either believes them or doesn't. Read the two `converge()`-shaped loops side by side: OSPF's speaker session widens each router's view of the *whole* topology one LSA at a time; this session's speaker never has a whole topology to look at, only ever the next hop's opinion.

## Toy Model Boundary

Real RIP speaks over UDP port 520, advertises on a periodic ~30-second timer (with triggered updates and jitter to avoid synchronized bursts), and applies split horizon per interface rather than per neighbor object. `converge()` here is synchronous and round-robin: every speaker's advertise phase for a round completes before any receive phase for that round begins, and the loop ends the instant one full round produces no table change anywhere — there is no timer, no packet loss, no partial delivery, and no interleaving of advertise and receive within a single round. `ToyRipSpeaker.neighbors` is a flat list of names with no interface, no link cost other than the implicit +1 hop, and no authentication. `lose_connected()` is the only failure mode modeled — no interface flap, no metric change short of total loss, no split-brain from asymmetric neighbor lists.

## Code Landmarks

### The module docstring's closing paragraph

"OSPF floods facts unchanged and each router recomputes shortest paths locally from a shared map... RIP never builds a map. It passes distance rumors hop by hop and trusts arithmetic... to eventually settle." This is the thesis of the whole RIP track, stated against the other half of the course. Read it before the class definition.

### `advertise_to()`

One line: `return advertisable(self.table, to_neighbor=neighbor)`. The capstone does not reimplement split horizon — it calls the Session 05 function directly, on every round, for every neighbor. The fix from Session 05 is not optional here; it is the only way `advertise_to()` knows how to speak.

### `receive()`

Delegates entirely to `process_advertisement()` from Session 02-03, then appends one trace line per `(prefix, outcome)` pair. The speaker adds no routing logic of its own here — it adds observability.

### `lose_connected()`

`self.table.routes[prefix] = poison(current)` — the route stays in the table, at `INFINITY`, rather than being popped. A speaker with a poisoned route still has something to say about that prefix on the next round; a speaker with a deleted route would simply go silent about it, which is a slower signal for neighbors to notice.

### `converge()`'s two-phase loop

The `outgoing` dict is fully built — every speaker, every neighbor — before any `receive()` call happens. This is what makes one round of `converge()` correspond to one synchronous round of "everyone speaks, then everyone listens," matching the round shape used in `count_to_infinity.py`'s hand-rolled two-router loop.

## Failure Questions

Use the source file to answer these:

1. `converge()` builds the entire `outgoing` dict before calling any `receive()`. What would change about the 3-speaker chain's `rounds_run` if `receive()` were instead called immediately after each `advertise_to()`, so a later speaker in the same round could see an already-updated table from an earlier one?
2. `advertise_to()` calls `advertisable()`, not `advertisable_with_poison()`. Given `lose_connected()`'s behavior, what would change about how fast the 3-speaker chain's poison round propagates if `advertise_to()` used poisoned reverse instead of plain split horizon?
3. `converge()` decides `changed` by comparing `speakers[receiver].table.routes != before` as a dict equality check. Why does a `UpdateOutcome.IGNORED_WORSE` outcome from `process_advertisement()` never cause `changed` to become `True`?
4. `lose_connected()` calls `self.connected.pop(prefix, None)` right after poisoning the route in `self.table.routes`. What is `connected` used for elsewhere in `ToyRipSpeaker`, and why does losing a prefix need to update it too?
5. `ConvergenceReport.converged` is `False` only when the `for round_no in range(1, rounds + 1)` loop exhausts every round without `changed` ever coming back `False`. Given that `count_to_infinity.py`'s unfiltered exchange takes 8 rounds to stabilize, what is the smallest `rounds` value you could pass to `converge()` on an *unfiltered* two-speaker version of that scenario and still see `converged=True`?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/rip/session_06_walkthrough.py
```

The walkthrough builds a 3-speaker chain X-Y-Z, where only X has a directly connected prefix, and runs `converge()` to confirm it stabilizes in 3 rounds with the metrics forming the expected 1/2/3 pattern down the chain. It checks that `Y`'s trace records an `"Adopted new route"` line and that traces are empty only where nothing was ever received (X has no upstream neighbor). It then calls `lose_connected()` on X, confirms the route is poisoned to `INFINITY` in place rather than deleted, runs `converge()` again, and confirms the poison reaches every speaker in the chain — with X's trace recording the loss event by name.

## Done When

The learner can say all of the following without looking at notes:

- "Every field and method on ToyRipSpeaker traces back to an earlier session; converge() only adds the round-robin exchange loop."
- "advertise_to() is not a simplified version of split horizon — it is Session 05's advertisable() called directly, every round, for every neighbor."
- "RIP's speaker gossips distances hop by hop and trusts arithmetic to converge; OSPF's speaker floods facts and recomputes shortest paths locally from a shared map. Same reachability problem, opposite philosophies."

## References

- RFC 2453 Section 3.9 (Response Processing)
- RFC 2453 Section 3.9.2 (the update rules `process_advertisement()` implements)
- RFC 2453 Section 2.3 (Split Horizon and Split Horizon with Poisoned Reverse, wired into `advertise_to()`)
- This course's OSPF track, `ospf/speaker.py` (Session 12 of the OSPF track) — the deliberate contrast: shared-map recomputation versus hop-by-hop rumor propagation, cited directly in this file's module docstring
