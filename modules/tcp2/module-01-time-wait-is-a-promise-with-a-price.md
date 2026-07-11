# Session 01 / Module 01: TIME_WAIT Is a Promise with a Price

## Position

- Track: TCP2
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/tcp2/module-01/index.html`
- Source file: `src/protocol_in_code/tcp2/time_wait_cost.py`
- Walkthrough script: `examples/tcp2/session_01_walkthrough.py`

## Core Question

Track 1 promised that every actively-closed connection lingers in TIME_WAIT for TWO_MSL ticks before its port is free again. What does that promise cost when you try to open connections fast?

## Outcome

By the end of this session, the learner should be able to:

- state the headline ceiling — roughly 68 connections per second to one destination — and derive it from `EPHEMERAL_PORTS / TWO_MSL`
- explain why `time_wait_slots()` is Little's Law applied to a queue with a fixed dwell time
- predict, without running code, what happens to the slot count when the connect rate doubles
- explain why `connect_would_fail()` is a >= comparison, not a > comparison

## Read Order

1. Read the module docstring and the `TWO_MSL` import comment
2. Read `EPHEMERAL_PORTS`
3. Read `time_wait_slots()`
4. Read `max_rate_to_one_destination()`
5. Read `connect_would_fail()`
6. Run `examples/tcp2/session_01_walkthrough.py`

## Read It Like Code

```python
time_wait_slots(rate_per_tick) -> int
max_rate_to_one_destination(ports=EPHEMERAL_PORTS) -> float
connect_would_fail(active_time_wait, ports=EPHEMERAL_PORTS) -> bool
```

There is no dataclass in this file. Every function takes plain numbers in and returns a plain number or bool out — the entire lesson is arithmetic, not state.

## Fields That Matter

| Name | Why it matters |
|---|---|
| `TWO_MSL` | Imported, not redefined. This file prices a number Session 09 of Track 1 already fixed at 240 ticks — the wait duration is not this file's decision to make. |
| `EPHEMERAL_PORTS` | The number of local ports available for outbound connections to one remote peer. Every port in TIME_WAIT is a port you cannot reuse yet. |
| `rate_per_tick` | The steady connect rate the caller is asking about. Not validated, not clamped — this is pure ratio arithmetic, garbage in, garbage out. |

## Decision Flow

```text
time_wait_slots(rate_per_tick):
    slots occupied = rate_per_tick * TWO_MSL      (Little's Law: N = rate * time-in-system)

max_rate_to_one_destination(ports):
    sustainable rate = ports / TWO_MSL             (invert the same relationship, solve for rate)

connect_would_fail(active_time_wait, ports):
    active_time_wait >= ports  -> True   (no port left to hand out)
    active_time_wait <  ports  -> False  (at least one port free)
```

## Reading Lens

Session 09 of Track 1 taught TIME_WAIT as a *state* — something a connection sits in, waiting for `now - entered_at >= TWO_MSL`. This session asks a different question about the same fact:

- if TWO_MSL ticks is fixed, and you keep opening and closing connections to the same peer, how many ports are occupied *at any one instant*?
- what breaks first — is it a timer, or is it a finite resource running out?
- is 68 connections/sec fast or slow, and to how many distinct peers does that ceiling actually apply?

The move is to stop treating TIME_WAIT as "a wait" and start treating it as "a lease on a scarce port," held for a fixed term.

## Toy Model Boundary

This file models exactly one destination: one `(local_ip, remote_ip, remote_port)` triple competing for the same 16384 ephemeral ports. Real systems open connections to many destinations concurrently, and a port used for peer A's TIME_WAIT is still free to reuse against peer B — the operating system's real ceiling is far more forgiving than this toy's single-destination number suggests, because reuse is scoped per-4-tuple, not global. This file does not model that; `max_rate_to_one_destination()` is deliberately the worst case, one peer, one port pool, no relief from talking to anyone else.

`rate_per_tick` is also a steady-state assumption — Little's Law only holds when arrivals are roughly constant. A bursty workload that opens 1000 connections in one tick and none for the next 239 will spike far above what `time_wait_slots()` predicts for its average rate, even though the long-run average matches.

## Code Landmarks

### The `TWO_MSL` import comment

The most important line in this file is a comment, not code: `from ..tcp.teardown import TWO_MSL`. Nothing here redefines what TWO_MSL means or how long it lasts — that was decided in Track 1. This file only asks what it costs to hold that promise at a given rate.

### `time_wait_slots()`

One multiplication: `rate_per_tick * TWO_MSL`. This is Little's Law (`L = λW`) with the variable names swapped for TCP: L is the slot count, λ is `rate_per_tick`, W is `TWO_MSL`.

### `max_rate_to_one_destination()`

The headline number. `ports / TWO_MSL` is `time_wait_slots()` solved backward: instead of asking "how many slots does this rate fill," it asks "what rate exactly fills every slot." With the defaults, that is `16384 / 240 ≈ 68.27` connections per second to one destination.

### `connect_would_fail()`

A single `>=` comparison. At `active_time_wait == ports`, every port is already parked in TIME_WAIT — the next `connect()` has nothing left to allocate, so this is already a failure, not the boundary of one.

## Failure Questions

Use the source file to answer these:

1. Where does `TWO_MSL` come from in this file — is it computed here, or imported? What file actually defines its value?
2. `time_wait_slots()` returns an `int`, but its input is a `float` multiplied by another value. What operation causes the truncation, and could it ever round a rate that should fail down to a slot count that looks safe?
3. If you double the argument to `time_wait_slots()`, what happens to its return value? Which single line of the function makes that true?
4. `connect_would_fail()` uses `>=`, not `>`. At `active_time_wait == ports` exactly, does the function say a connect would fail? Why does that make sense in terms of ports available to hand out?
5. `max_rate_to_one_destination()` takes `ports` as a parameter with a default of `EPHEMERAL_PORTS`. What would calling it with a smaller `ports` value represent about the environment it's modeling?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tcp2/session_01_walkthrough.py
```

The walkthrough computes the 68.27/sec headline live from the same division shown in the docstring, checks that `time_wait_slots()` at that exact rate fills every port, halves the rate to show half the slots occupied, doubles it back to show the linear relationship, and flips `connect_would_fail()` right at the port-count boundary.

## Done When

The learner can say all of the following without looking at notes:

- "TIME_WAIT isn't just a wait — it's a lease on a port, and the lease term is TWO_MSL from Track 1."
- "The ceiling is ports divided by wait time; double the wait or halve the ports and the ceiling drops the same way."
- "This is a worst case for one destination — real systems don't hit this ceiling nearly as fast because reuse is scoped per-peer."

## References

- RFC 9293 Section 3.6 (Wait Time for MSL, i.e. TIME-WAIT — the origin of the TWO_MSL duration this file prices)
