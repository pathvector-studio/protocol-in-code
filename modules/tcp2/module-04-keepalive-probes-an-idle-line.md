# Session 04 / Module 04: Keepalive Probes an Idle Line

## Position

- Track: TCP2
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/tcp2/module-04/index.html`
- Source file: `src/protocol_in_code/tcp2/keepalive.py`
- Walkthrough script: `examples/tcp2/session_04_walkthrough.py`

## Core Question

If a TCP connection goes silent and neither side sends a FIN or RST, who notices it is dead, and how long does that take?

## Outcome

By the end of this session, the learner should be able to:

- name the three classic Linux keepalive constants and what each one governs
- compute the clock time of any of the nine probes from `last_activity` alone
- explain why a single answered probe is enough to call the connection ALIVE again
- state why the connection is declared DEAD at exactly the ninth probe's time, not before
- explain why a 7200-second default keepalive is often too slow to matter against a NAT mapping

## Read Order

1. Read the module comment above `KEEPALIVE_IDLE` — the classic Linux defaults and the NAT-mismatch note
2. Read `KEEPALIVE_IDLE`, `KEEPALIVE_INTERVAL`, `KEEPALIVE_COUNT`
3. Read `KeepaliveVerdict`
4. Read `probe_times()`
5. Read `connection_verdict()`
6. Run `examples/tcp2/session_04_walkthrough.py`

## Read It Like Code

```python
probe_times(last_activity) -> tuple[int, ...]
connection_verdict(last_activity, probe_replies, now) -> KeepaliveVerdict
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `KEEPALIVE_IDLE` | 7200 seconds. How long the connection must be silent before the first probe is even sent. |
| `KEEPALIVE_INTERVAL` | 75 seconds. The spacing between probes once probing starts. |
| `KEEPALIVE_COUNT` | 9. How many consecutive unanswered probes it takes to call the connection dead. |
| `probe_replies` | One bool per probe sent so far, in `probe_times()`'s order. A single `True` anywhere in it means ALIVE. |

## Decision Flow

```text
connection_verdict(last_activity, probe_replies, now):
  times = probe_times(last_activity)          # 9 clock times, first at last_activity + 7200

  now < times[0]                               -> ALIVE    (still inside the idle window, no probe due yet)
  any(probe_replies)                           -> ALIVE    (any reply so far cancels the death spiral)
  len(probe_replies) >= 9 and now >= times[8]  -> DEAD      (nine unanswered probes, and time has caught up to the ninth)
  otherwise                                     -> PROBING  (between the first probe and a verdict)
```

## Reading Lens

The important move in this session is to stop treating "the connection is idle" as a single fact and start asking, at every point in the schedule:

- what clock time is `now`, relative to `times[0]` and `times[8]`?
- has *any* probe been answered, or are all of them still silent?
- how many probes have actually fired by `now` — is `len(probe_replies)` even at 9 yet?

Session 05 of the NAT track (`modules/nat/module-05-state-expires-again.md`, source `nat/timeout.py`) is the cross-reference this session needs: `nat/timeout.py`'s `EXPIRY_SECONDS["udp"]` is 30 seconds and its TCP entry is trusted for 300 seconds — both dramatically shorter than `KEEPALIVE_IDLE`'s 7200. A NAT mapping for this same connection can be reclaimed by the middlebox in under a minute (UDP) or a few minutes (TCP), long before `probe_times()`'s first probe is even due. The keepalive is not wrong about the connection's state — it is simply too slow to arrive before the path itself has been torn down underneath it. This is the same "state expires quietly, and nobody was told" shape as Session 05 of NAT, just measured on the other side of the mapping, at ten to over two-hundred times the timescale.

## Toy Model Boundary

Real systems let each socket override `KEEPALIVE_IDLE`, `KEEPALIVE_INTERVAL`, and `KEEPALIVE_COUNT` individually via `SO_KEEPALIVE` and `TCP_KEEPIDLE`/`TCP_KEEPINTVL`/`TCP_KEEPCNT` (or platform equivalents) — this module hardcodes the three classic Linux defaults as module-level constants, so every connection in this course shares one schedule. `probe_times()` and `connection_verdict()` are pure functions of `last_activity`, `probe_replies`, and `now` — there is no actual probe being sent on the wire, no packet loss model, and no distinction between "probe was never sent" and "probe was sent but its reply hasn't arrived yet by `now`." A real kernel's keepalive timer also resets on any traffic at all, not just an explicit "activity" event; this toy takes `last_activity` as a given integer rather than deriving it from a stream of segments.

## Code Landmarks

### The module comment above `KEEPALIVE_IDLE`

States the classic Linux defaults plainly and immediately points at `nat/timeout.py` for the mismatch — read this before the constants themselves, because the constants only make sense against that comparison.

### `probe_times()`

One line of arithmetic: `first = last_activity + KEEPALIVE_IDLE`, then 9 evenly spaced entries `KEEPALIVE_INTERVAL` apart. Every other function in this file reads its answer off this schedule; nothing here has its own notion of time.

### `connection_verdict()`

Four branches, checked in order. Notice `any(probe_replies)` is checked *before* the DEAD condition — a reply anywhere in the tuple short-circuits straight to ALIVE, even if eight other probes in the same tuple went unanswered.

## Failure Questions

Use the source file to answer these:

1. `last_activity = 0`. At `now = 8799` (one tick before the ninth probe time), with all eight probes fired so far unanswered, what does `connection_verdict()` return? What about at `now = 8800`?
2. `probe_replies = (False, False, False, False, True, False, False, False, False)` and `now` is at or past `times[8]`. What verdict does `connection_verdict()` return, and which line in the function decides it?
3. Why does `probe_times()` take only `last_activity` as an argument — where do `KEEPALIVE_INTERVAL` and `KEEPALIVE_COUNT` come from instead?
4. At `now = last_activity + 7199`, one second before the idle window ends, what does `connection_verdict()` return regardless of what `probe_replies` contains?
5. `connection_verdict()`'s DEAD branch requires both `len(probe_replies) >= KEEPALIVE_COUNT` and `now >= times[KEEPALIVE_COUNT - 1]`. Construct a case where `len(probe_replies) >= 9` is true but `now < times[8]` — what verdict does that case return, and why does the function need both conditions instead of just the length check?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tcp2/session_04_walkthrough.py
```

The walkthrough checks `probe_times()`'s arithmetic directly, then shows ALIVE before the idle window elapses, PROBING partway through the probe sequence, DEAD at the exact ninth-probe boundary, ALIVE again after a single answered probe, and closes on the NAT-mismatch numbers: 30 seconds (UDP mapping) and 7200 seconds (keepalive idle) side by side.

## Done When

The learner can say all of the following without looking at notes:

- "probe_times() is nine clock times: the first at last_activity + 7200, each of the rest 75 seconds after the last."
- "A single answered probe anywhere in probe_replies is enough to call the connection ALIVE again — death requires nine in a row, all silent."
- "DEAD fires at exactly the ninth probe's time, not one tick sooner."
- "7200 seconds is longer than almost any NAT mapping's timeout, so a keepalive can be technically correct and still arrive after the path is already gone."

## References

- RFC 1122 Section 4.2.3.6 (TCP Keep-Alives)
