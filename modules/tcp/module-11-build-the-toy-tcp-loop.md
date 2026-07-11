# Session 11 / Module 11: Build the Toy TCP Loop

## Position

- Track: TCP
- Session: 11
- Site lesson: `pathvector-site/courses/protocols-in-code/tcp/module-11/index.html`
- Source file: `src/protocol_in_code/tcp/speaker.py`
- Walkthrough script: `examples/tcp/session_11_walkthrough.py`

## Core Question

What does one endpoint's whole life look like when handshake, data delivery, congestion, reset, and teardown are all wired into a single object instead of ten separate demos?

## Outcome

By the end of this session, the learner should be able to:

- name every field on `ToyTcpEndpoint` and which earlier session's module owns it
- explain why `state` holds two different enum types over one connection's life, and why that seam exists on purpose
- trace `on_segment()`'s dispatch order and say why `on_reset()` runs before anything state-specific
- run two endpoints through handshake, one data transfer, and a full active close to `CLOSED`, reading the trace as the source of truth

## Read Order

1. Read the module comment above `ToyTcpEndpoint` about the two enum spaces
2. Read `ToyTcpEndpoint`'s field list top to bottom
3. Read `tick()`
4. Read `listen()` and `active_open()`
5. Read `on_segment()` top to bottom — this is the whole track's dispatch table
6. Read `_on_data()` and `_on_segment_teardown()`
7. Read `close()`
8. Read `run_three_way_handshake()`
9. Run `examples/tcp/session_11_walkthrough.py`

## Read It Like Code

```python
ToyTcpEndpoint(
    name,
    iss,
    state,
    clock,
    rcv_nxt,
    recv_buffer,
    reassembly,
    estimator,
    congestion,
    ack_tracker,
    time_wait_entered_at,
    trace,
)
```

## Parts List

Every field and every function `speaker.py` imports was taught by an earlier session in this track. The capstone's only new code is the wiring between them.

| Import | Session that taught it | What it contributes to `ToyTcpEndpoint` |
|---|---|---|
| `segment.Segment`, `is_fin`, `is_rst`, `flags_label` | 01 | The wire unit every function below reads or writes. |
| `handshake.ConnectionState`, `active_open`, `on_segment` | 02 | `state`'s first enum space; drives `active_open()` and the pre-ESTABLISHED half of `on_segment()`. |
| `seqnum` (via `window.py`'s `in_receive_window`, used inside `reset.py`) | 03 | The ring arithmetic underneath both the receive window and reset's window check. |
| `window.ReceiveBuffer`, `advertised_window` | 04 | `recv_buffer`; its `advertised_window()` feeds directly into `on_reset()`'s window check. |
| `rto.RttEstimator` | 05 | `estimator` — present on every endpoint, though this capstone's walkthrough does not exercise `observe()`. |
| `fast_retransmit.AckTracker`, `on_ack` (imported as `track_ack`), `AckSignal` | 06 | `ack_tracker`; `_on_data()` calls it on every data segment to watch for duplicate acks. |
| `congestion.CongestionState`, `on_ack`, `on_timeout` | 07 | `congestion`; `_on_data()` grows or resets `cwnd` depending on what `track_ack()` reports. |
| `reassembly.ReassemblyBuffer`, `deliver` | 08 | `reassembly`; created the moment the handshake reaches `ESTABLISHED`, and every data segment after that flows through `deliver()`. |
| `reset.ResetDisposition`, `on_reset` | 10 | The very first check in `on_segment()`, run before any state-specific branch — see Decision Flow. |
| `teardown.CloseState`, `initiate_close`, `on_segment_active`, `on_segment_passive`, `passive_close` | 09 | `state`'s second enum space; drives `close()` and the post-ESTABLISHED half of `on_segment()`. |

Session 10 (`reset.py`) is read before Session 09 (`teardown.py`) in this table because `on_segment()` checks it first — but the module numbering in this track is unaffected; Session 09 is still taught before Session 10.

## Decision Flow

```text
on_segment(segment):
  1. on_reset(state, segment, rcv_nxt, advertised_window(recv_buffer))
       ACCEPTED  -> state = CloseState.CLOSED, trace it, return None   (stop here, unconditionally)
       otherwise -> fall through, state is untouched
  2. state is a ConnectionState and not yet ESTABLISHED
       -> dispatch to handshake.on_segment(); on reaching ESTABLISHED,
          set rcv_nxt from the final segment and create `reassembly`
  3. state is a CloseState
       -> _on_segment_teardown():
            state is CLOSE_WAIT              -> no-op (only close() moves this forward)
            state is LAST_ACK                -> on_segment_passive()
            state is FIN_WAIT_1/2 or CLOSING  -> on_segment_active()
  4. state is ConnectionState.ESTABLISHED and segment carries a FIN
       -> on_segment_passive(CloseState.ESTABLISHED, segment): CLOSE_WAIT
  5. otherwise (ESTABLISHED, data segment)
       -> _on_data(): deliver() into reassembly, then track_ack() and
          feed congestion.on_ack() or congestion.on_timeout()
```

## Reading Lens

The important move in this session is to stop reading each module in isolation and start asking, at every line of `on_segment()`:

- which of the eleven imported names is doing the actual work on this line, and which session taught that name?
- what type is `self.state` right now — a `ConnectionState` or a `CloseState`? The two enums never mix, but one field holds both.
- what changed in `self.trace` as a result of this call, and would that line alone tell a debugger what happened?

## Toy Model Boundary

`MSS = 1` — every data segment in this module's own tests and the walkthrough is one byte, which keeps `reassembly.py`'s sequence arithmetic readable but means nothing here demonstrates real segmentation. `state: object = ConnectionState.CLOSED` is typed as `object`, not `ConnectionState | CloseState` — the comment above the class explains why: `CloseState.ESTABLISHED` and `ConnectionState.ESTABLISHED` are two enum members that mean the same connection moment, kept as two separate enums so each session's file stays independent of the others, and `ToyTcpEndpoint` is the one place that has to reconcile them. That reconciliation is a design seam worth teaching on its own, not a bug to paper over. There is no retransmission timer wired to `estimator` or `rto.py` in this module — `RttEstimator` is constructed on every endpoint but `observe()` is never called from `on_segment()` or `tick()`. Passive close is only reachable through the `close()` method's `CLOSE_WAIT` branch, which a test or walkthrough must call explicitly; nothing in `on_segment()` calls it automatically. `run_three_way_handshake()` only demonstrates the handshake — it does not drive either endpoint through data, reset, or teardown.

## Code Landmarks

### The comment above `ToyTcpEndpoint`

The clearest single explanation in the whole track of why one field can legally hold two unrelated enum types. Read it before reading the class.

### `on_segment()`'s first statement

`on_reset(...)` runs unconditionally, before the function even checks what `self.state` is. A RST is checked against every state the same way — including mid-handshake — because `on_reset()` takes `rcv_nxt` and `window` as plain arguments, not connection-state-aware ones.

### `_on_segment_teardown()`'s routing comment

"LAST_ACK belongs to the passive closer's path; every other close state here ... belongs to the active closer's path." This one `if` is the entire bridge between `teardown.py`'s two independent functions.

### `tick()`

The only place `time_wait_expired()` is called from inside `speaker.py`. Advancing the clock is the only way `TIME_WAIT` ever resolves to `CLOSED` — no segment does it.

### `close()`

One method, two behaviors, chosen by `self.state`. `CLOSE_WAIT` routes to `passive_close()`; anything else routes to `initiate_close()`. Both build a FIN the same way; only the resulting `CloseState` differs.

## Failure Questions

Use the source file to answer these:

1. `on_segment()` calls `on_reset()` before checking whether `self.state` is a `ConnectionState` or a `CloseState`. What `rcv_nxt` value does a RST get checked against if it arrives while the connection is still in `SYN_SENT`, before any data has ever been received?
2. In `_on_segment_teardown()`, why does `LAST_ACK` need its own `if` branch instead of falling into the same `on_segment_active()` call as `FIN_WAIT_1`, `FIN_WAIT_2`, and `CLOSING`?
3. `on_segment()` sets `self.rcv_nxt` and creates `self.reassembly` only inside the branch that reaches `ConnectionState.ESTABLISHED`. What would happen if a data segment arrived one call earlier, while `self.reassembly` is still `None`?
4. `tick()` checks `self.state is CloseState.TIME_WAIT` before calling `time_wait_expired()`. What happens to `self.time_wait_entered_at` on every other state — does `tick()` ever clear it?
5. `_on_data()` calls `track_ack()` on every data segment, then checks the returned `AckSignal`. Which of the three `AckSignal` values causes no change to `congestion`'s `cwnd` at all?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tcp/session_11_walkthrough.py
```

The walkthrough builds a client and a server `ToyTcpEndpoint`, runs `run_three_way_handshake()` so both reach `ESTABLISHED`, delivers one data segment and checks `rcv_nxt` advanced on the receiving side, drives the client through an active close — `close()`, the peer's replies, `tick()` past `TWO_MSL` — until both endpoints report `CLOSED`, and finally checks that both endpoints' `trace` lists are non-empty and contain the lines that mark the handshake and the close.

## Done When

The learner can say all of the following without looking at notes:

- "Every field on ToyTcpEndpoint belongs to an earlier session; this module only wires them together in on_segment()."
- "state holds a ConnectionState before ESTABLISHED and a CloseState after — two enum spaces, one field, on purpose."
- "on_reset() runs first, unconditionally, before any state-specific branch — a RST is checked the same way no matter what the connection is doing."

## References

- RFC 9293 Section 3.3 (state machine overview)
- RFC 9293 Section 3.5 (Closing a Connection)
- RFC 9293 Section 3.5.3 (Reset Processing)
