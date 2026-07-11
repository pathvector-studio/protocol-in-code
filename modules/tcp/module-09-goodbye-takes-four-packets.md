# Session 09 / Module 09: Goodbye Takes Four Packets (and a Wait)

## Position

- Track: TCP
- Session: 09
- Site lesson: `pathvector-site/courses/protocols-in-code/tcp/module-09/index.html`
- Source file: `src/protocol_in_code/tcp/teardown.py`
- Walkthrough script: `examples/tcp/session_09_walkthrough.py`

## Core Question

Why does closing a TCP connection take four segments and a wait, instead of ending the moment one side is done talking?

## Outcome

By the end of this session, the learner should be able to:

- name the eight `CloseState` values and say which side (active or passive) ever visits each one
- walk the active closer through FIN_WAIT_1, FIN_WAIT_2, and TIME_WAIT, and count exactly four segments on the wire
- walk the passive closer through CLOSE_WAIT and LAST_ACK to CLOSED
- explain why TIME_WAIT is a duration, not a state that ends when a segment arrives

## Read Order

1. Read `CloseState`
2. Read `TeardownStep`
3. Read `initiate_close()`
4. Read `on_segment_active()`
5. Read `on_segment_passive()`
6. Read `passive_close()`
7. Read `time_wait_expired()`
8. Run `examples/tcp/session_09_walkthrough.py`

## Read It Like Code

```python
TeardownStep(
    new_state,
    reply,
    note,
    wait_started_at,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `new_state` | Where this side lands after processing the segment (or the local `close()` call). |
| `reply` | The segment to send back, or `None` when this step only changes local state. |
| `note` | A one-line trace of what just happened — the habit this whole track teaches. |
| `wait_started_at` | Set only on the transition into `TIME_WAIT`. Everything about the wait is computed from this one stamp. |

## Decision Flow

```text
Active closer (initiate_close then on_segment_active):
  ESTABLISHED  --initiate_close()-->        FIN_WAIT_1
  FIN_WAIT_1   --peer FIN+ACK-->            TIME_WAIT   (reply: ACK)
  FIN_WAIT_1   --peer ACK only-->           FIN_WAIT_2
  FIN_WAIT_1   --peer FIN (no ACK yet)-->   CLOSING     (reply: ACK, simultaneous close)
  FIN_WAIT_2   --peer FIN-->                TIME_WAIT   (reply: ACK)
  CLOSING      --peer ACK-->                TIME_WAIT
  TIME_WAIT    --now - entered_at >= TWO_MSL-->  CLOSED (time_wait_expired(), no segment involved)

Passive closer (on_segment_passive then passive_close):
  ESTABLISHED  --peer FIN-->                CLOSE_WAIT  (reply: ACK)
  CLOSE_WAIT   --local close()-->           LAST_ACK    (reply: FIN, via passive_close())
  LAST_ACK     --peer ACK-->                CLOSED
```

## Reading Lens

The important move in this session is to stop thinking "closing a connection" is one event and start asking:

- which side sent the first FIN — am I reading the active path or the passive path?
- has this side's own FIN been acked yet, independent of whether the peer's FIN has arrived?
- if this step lands in `TIME_WAIT`, what was `wait_started_at`, and how far is `now` from it?

## Toy Model Boundary

This module models one full close per connection, driven by real segments. It does not retransmit a FIN that gets no ACK — a real stack would time out and resend `initiate_close()`'s FIN; here, `on_segment_active()` simply stays in `FIN_WAIT_1` and waits again. Simultaneous close is present in a limited form: `on_segment_active()` handles a FIN arriving in `FIN_WAIT_1` before the peer's ACK by moving to `CLOSING`, but the module has no test of the mirror case starting from the passive side, because `on_segment_passive()` never observes a FIN while it is itself in a pre-FIN state (its first branch is keyed on `ESTABLISHED`). Half-close (an application that keeps sending data after receiving a FIN) is not modeled — the passive side's `CLOSE_WAIT` branch never inspects payload. `TWO_MSL` is an abstract integer of ticks, not a real duration in seconds; the walkthrough treats it purely as a threshold to compare `now` against.

## Code Landmarks

### `TWO_MSL`

A bare module constant, `240`. It is never described as seconds anywhere in the source — the whole module treats time as ticks on a clock argument, which is what makes `time_wait_expired()` a pure comparison instead of a real timer.

### `on_segment_active()`

The active closer's three states share one function, dispatched by `state`. The `FIN_WAIT_1` branch is the busiest: it must distinguish "peer FIN+ACK together" from "peer ACK alone" from "peer FIN alone" (simultaneous close) from "neither yet," and each of the first three ends in a different state.

### `on_segment_passive()`

Three branches, but `CLOSE_WAIT`'s branch does nothing to `state` — the comment says exactly why: only the local application's `close()` call (modeled as `passive_close()`, driven from the speaker capstone) moves this side out of `CLOSE_WAIT`. No incoming segment can do it.

### `time_wait_expired()`

One comparison: `now - entered_at >= TWO_MSL`. Nothing else in the module reads `TIME_WAIT` — the entire "how long do we linger" question is this one line.

## Failure Questions

Use the source file to answer these:

1. At exactly `now == entered_at + TWO_MSL`, does `time_wait_expired()` return `True` or `False`? Which comparison operator decides?
2. If the active closer is in `FIN_WAIT_1` and receives a segment that is a FIN but not also an ACK, which state does `on_segment_active()` choose, and what note does it attach?
3. Why does `on_segment_passive()`'s `CLOSE_WAIT` branch return the same `state` it was given instead of advancing, even though a segment did arrive?
4. `initiate_close()` and `passive_close()` both build a FIN the same way (same `seq`, `ack=0`, `flags={"FIN"}`). What is different about the two `CloseState` values each one returns to?
5. Which `CloseState` values does `on_segment_active()` ever return, and which does `on_segment_passive()` ever return? Is there any state both functions handle?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tcp/session_09_walkthrough.py
```

The walkthrough drives one connection through the full four-segment active close — FIN, FIN+ACK-equivalent replies, and the final ACK — counts exactly four segments crossing the wire, drives the passive side through CLOSE_WAIT and LAST_ACK to CLOSED, and shows `time_wait_expired()` flip from `False` to `True` at the `TWO_MSL` boundary.

## Done When

The learner can say all of the following without looking at notes:

- "Closing needs four segments because each side's FIN and each side's ACK are independent events."
- "TIME_WAIT is not waiting for a segment — it is waiting for time, arithmetic on `entered_at + TWO_MSL`."
- "CLOSE_WAIT only ever advances because the local application called close(), never because a segment arrived."

## References

- RFC 9293 Section 3.5 (Closing a Connection)
- RFC 9293 Section 3.6 (Wait Time for MSL, i.e. TIME-WAIT)
