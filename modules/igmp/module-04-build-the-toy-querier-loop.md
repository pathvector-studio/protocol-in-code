# Session 04 / Module 04: Build the Toy Querier Loop

## Position

- Track: IGMP
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/igmp/module-04/index.html`
- Source file: `src/protocol_in_code/igmp/querier_loop.py`
- Walkthrough script: `examples/igmp/session_04_walkthrough.py`

## Core Question

What does one full query cycle look like end to end — router and switch together — when a host goes quiet and the forwarding set actually has to shrink because of it?

## Outcome

By the end of this session, the learner should be able to:

- name every function `querier_loop.py` imports and which earlier session's module owns it
- trace `run_query_cycle()`'s two query cycles in order and say what changes the router's and the switch's state at each step
- explain why the BEFORE forwarding set includes a port the AFTER set does not, and which two function calls are responsible
- run `ToyQuerier` and `ToySnoopingSwitch` through a full cycle and read the trace as the source of truth for what happened and when

## Read Order

1. Read `QUERIER_PORT`
2. Read `ToyQuerier`'s field list and its four methods
3. Read `ToySnoopingSwitch`'s field list and its four methods
4. Read `run_query_cycle()`'s docstring
5. Read `run_query_cycle()` top to bottom, step by step against the docstring's six-step list
6. Run `examples/igmp/session_04_walkthrough.py`

## Read It Like Code

```python
ToyQuerier(
    table,
    state,
    clock,
    trace,
)

ToySnoopingSwitch(
    table,
    trace,
)
```

## Parts List

Every function `querier_loop.py` imports was taught by an earlier session in this track. The capstone's only new code is the wiring between them — `ToyQuerier`, `ToySnoopingSwitch`, and the six-step cycle in `run_query_cycle()`.

| Import | Session that taught it | What it contributes to the capstone |
|---|---|---|
| `membership.GroupTable`, `join` | 01 | `ToyQuerier.table`; `receive_report()` calls `join()` on every report, so a reporting host becomes a member the same way Session 01 modeled it. |
| `querier.MembershipState`, `on_report`, `expire_silent`, `report_suppression`, `MEMBERSHIP_TIMEOUT`, `QUERY_INTERVAL` | 02 | `ToyQuerier.state`; `receive_report()` calls `on_report()`, `expire()` calls `expire_silent()`, and `run_query_cycle()` calls `report_suppression()` whenever a group has more than one interested member. |
| `snooping.SnoopingTable`, `forward_ports`, `observe_query`, `observe_report` | 03 | `ToySnoopingSwitch.table`; `hear_query()`/`hear_report()` call `observe_query()`/`observe_report()`, and `forwarding_set()` calls `forward_ports()` directly. |

## Decision Flow

```text
run_query_cycle(querier, switch, hosts, silent_hosts):
  1. querier.general_query()                 -> trace: query sent at clock=0
     switch.hear_query(QUERIER_PORT)          -> switch.table.querier_port = 0

  2. for each group, every member reports at least once (report_suppression()
     picks the single responder when a group has more than one member):
       querier.receive_report(group, responder) -> join() + on_report(), both at clock=0
       switch.hear_report(port, group)           -> observe_report()

  3. BEFORE snapshot: switch.forwarding_set(watched_group, all_ports)

  4. querier.tick(QUERY_INTERVAL)             -> clock=125
     querier.general_query(); switch.hear_query(QUERIER_PORT)
     only non-silent hosts report this cycle   -> on_report() at clock=125 for them only

  5. querier.clock = MEMBERSHIP_TIMEOUT        -> clock=260
     querier.expire()                          -> expire_silent(): anyone silent since
                                                   clock=0 is now past MEMBERSHIP_TIMEOUT
     for each expired (group, host): switch.prune(group, host_port)

  6. AFTER snapshot: switch.forwarding_set(watched_group, all_ports)
     len(after) < len(before) -> trace: "shrank: someone stopped answering..."
```

## Reading Lens

The important move in this session is to stop reading `membership.py`, `querier.py`, and `snooping.py` as three separate stories and start reading `run_query_cycle()` as the one story that was always underneath them: a router asks, hosts answer (or don't), the router notices who went quiet, and a switch — watching the same wire, understanding none of the protocol semantics — mirrors that discovery into its own forwarding table. Ask, at every line of `run_query_cycle()`:

- which of the two objects (`querier` or `switch`) does this line mutate, and which earlier session's function is actually doing the work?
- what is `querier.clock` at this point in the function, and does that match the trace line just printed?
- if this line were deleted, which trace line downstream would stop appearing — the suppression line, the expiry line, or the prune line?

## Toy Model Boundary

One router, one switch, one query cycle repeated twice — there is no querier election (RFC 2236's lowest-IP-wins mechanism is entirely absent), and nothing here models multiple queriers on a segment or a querier going silent itself. `report_suppression()` always deterministically picks the first name in the members tuple; there is no random suppression timer and no "hears another report, cancels its own timer" simulated as a race — the outcome is just asserted. The clock in `run_query_cycle()` is manually driven with `querier.tick()` and a direct assignment (`querier.clock = MEMBERSHIP_TIMEOUT`) rather than advancing one query interval at a time, so real deployments' steady drip of query cycles is compressed to exactly the two moments this walkthrough needs. Hosts are names, not IP addresses, and ports are bare integers with no notion of a VLAN or a trunk.

## Code Landmarks

### `ToyQuerier.expire()`

The one method that produces a trace line naming a clock value in the past: `f"...silent since before clock={self.clock - MEMBERSHIP_TIMEOUT}..."`. Read this next to `querier.py`'s `expire_silent()` — this method is purely a tracing wrapper around it, with no independent logic.

### `ToySnoopingSwitch.prune()`

The docstring is the landmark: "Mirror an expiry the querier reported: the switch's own copy of interest shrinks too." The switch never decides on its own that a host is gone — it only ever prunes in direct response to something `expire()` already found.

### `run_query_cycle()`'s watched-group selection

`next((group for group, members in members_by_group.items() if any(h in silent_hosts for h in members)), ...)`. This line is what makes the BEFORE/AFTER snapshots meaningful — it deliberately picks the group with something to lose, rather than an arbitrary one.

### The `report_suppression()` call inside the first cycle's loop

`if len(members) > 1: responder = report_suppression(...)`. This is where Session 02's suppression mechanism gets exercised for real, inside a multi-host scenario, rather than as an isolated unit call.

### The BEFORE/AFTER shrink check

`if len(after) < len(before): querier.trace.append(...)`. The whole capstone's payoff is this one comparison — the forwarding set is smaller not because anything explicitly left, but because nobody answered the second query.

## Failure Questions

Use the source file to answer these:

1. `run_query_cycle()` advances the clock with `querier.tick(QUERY_INTERVAL)` for the second cycle, then later sets `querier.clock = MEMBERSHIP_TIMEOUT` directly instead of ticking again. Why does the comment say this measures the timeout "from the *first* cycle's reports," and what would break if the second assignment used `tick()` instead?
2. For a group with exactly one interested member, does `run_query_cycle()` ever call `report_suppression()` for that group? Which line decides?
3. `ToySnoopingSwitch.prune()` is called once per expired `(group, host)` pair. What port does it prune, and where does that port number come from — is it looked up fresh, or carried from earlier in `run_query_cycle()`?
4. The BEFORE snapshot is taken before the second query cycle begins, and the AFTER snapshot is taken after `expire()` and every resulting `prune()` call. If a host silent in the second cycle had, in fact, answered the very first query, would it still show up in the AFTER set? Trace `receive_report()` and `on_report()` to justify the answer.
5. `querier.trace` and `switch.trace` are two separate lists. Is there a single line in either trace that proves the router and the switch agree on what happened, or does the reader have to compare the two traces by hand to confirm that?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/igmp/session_04_walkthrough.py
```

The walkthrough builds a `ToyQuerier` and a `ToySnoopingSwitch`, sets up three hosts — two sharing a group behind different ports, one alone on its own group — and marks the lone host silent for the second cycle. It runs `run_query_cycle()`, prints both traces in full, then asserts: the suppression line reports 1 message saved for the 2-member group; the expiry line names the silent host and the clock reached 260; the BEFORE forwarding set is `(0, 3)` and the AFTER set is `(0,)`; the trace names the shrink; and the switch's trace contains the exact prune line for the silent host's port.

```text
Session 04 walkthrough: Build the toy querier loop

    querier: general query sent at clock=0
    querier: 224.0.1.5 has 2 interested members ('host-a', 'host-b'), suppression -> only host-a reports, 1 message(s) saved
    querier: report host-a -> 224.0.1.5 at clock=0
    querier: report host-c -> 224.0.2.9 at clock=0
    forwarding[224.0.2.9] BEFORE expiry: ports=(0, 3)
    querier: general query sent at clock=125
    querier: report host-a -> 224.0.1.5 at clock=125
    querier: clock advanced to 260 (past MEMBERSHIP_TIMEOUT since the first cycle)
    querier: host-c silent since before clock=0, expired from 224.0.2.9
    forwarding[224.0.2.9] AFTER expiry:  ports=(0,)
    forwarding[224.0.2.9] shrank: someone stopped answering, so the switch stopped forwarding to them
    switch: query overheard on port 0, querier_port=0
    switch: report overheard on port 1 for 224.0.1.5
    switch: report overheard on port 3 for 224.0.2.9
    switch: query overheard on port 0, querier_port=0
    switch: report overheard on port 1 for 224.0.1.5
    switch: port 3 pruned from 224.0.2.9 (querier expired the member behind it)

[OK] suppression saved 1 message for the 2-member group -> querier: 224.0.1.5 has 2 interested members ('host-a', 'host-b'), suppression -> only host-a reports, 1 message(s) saved
[OK] host-c expired at clock=260 -> querier: host-c silent since before clock=0, expired from 224.0.2.9
[OK] forwarding set BEFORE expiry -> forwarding[224.0.2.9] BEFORE expiry: ports=(0, 3)
[OK] forwarding set AFTER expiry  -> forwarding[224.0.2.9] AFTER expiry:  ports=(0,)
[OK] trace names the shrink        -> forwarding[224.0.2.9] shrank: someone stopped answering, so the switch stopped forwarding to them
[OK] switch prune line             -> switch: port 3 pruned from 224.0.2.9 (querier expired the member behind it)
```

## Done When

The learner can say all of the following without looking at notes:

- "Every field and method on `ToyQuerier` and `ToySnoopingSwitch` is a thin wrapper over a function taught in Sessions 01 through 03 — this session only wires the call order."
- "The router discovers a silent host by running `expire_silent()` on a schedule; the switch never discovers anything on its own — it only mirrors the router's discovery with `prune()`."
- "The forwarding set shrinking from `(0, 3)` to `(0,)` is the whole track's payoff: nobody explicitly left, but silence past `MEMBERSHIP_TIMEOUT` is treated exactly like a leave, all the way down to which switch ports get the traffic."

## References

- RFC 2236 Section 1 (Introduction — the querier/host/switch interaction this module wires end to end)
- RFC 2236 Section 3 (message formats: General Query, Membership Report, and the timers `QUERY_INTERVAL` and `MEMBERSHIP_TIMEOUT` model)
- RFC 2236 Section 6 (host state diagram — report suppression, modeled here by `report_suppression()`)
