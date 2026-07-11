# Session 10 / Module 10: RST Ends Everything Now

## Position

- Track: TCP
- Session: 10
- Site lesson: `pathvector-site/courses/protocols-in-code/tcp/module-10/index.html`
- Source file: `src/protocol_in_code/tcp/reset.py`
- Walkthrough script: `examples/tcp/session_10_walkthrough.py`

## Core Question

Teardown takes four packets and a wait — so what does a connection that ends with a RST skip, and what decides whether a RST is even allowed to end it?

## Outcome

By the end of this session, the learner should be able to:

- name the three `ResetDisposition` outcomes and which one applies to a non-RST segment
- explain what "in-window" means for a RST's sequence number, and why it is checked at all
- state what happens to `state` in each of the three outcomes
- contrast a RST's effect on a connection with the four-packet, patient path in `teardown.py`

## Read Order

1. Read `ResetDisposition`
2. Read `ResetOutcome`
3. Read `on_reset()`
4. Compare `on_reset()`'s ACCEPTED branch against `teardown.py`'s `initiate_close()` / `on_segment_active()` path
5. Run `examples/tcp/session_10_walkthrough.py`

## Read It Like Code

```python
ResetOutcome(
    disposition,
    new_state,
    note,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `disposition` | One of `ACCEPTED`, `IGNORED`, `NOT_A_RESET` — the only three ways `on_reset()` can end. |
| `new_state` | A plain string, `"Closed"` on acceptance or the untouched input `state` otherwise. Callers compare it by value, not by enum identity. |
| `note` | The same one-line trace habit as every other module in this track. |

## Decision Flow

```text
segment has no RST flag                         -> NOT_A_RESET, state unchanged
segment has RST, seq in [rcv_nxt, rcv_nxt+window) -> ACCEPTED, state -> "Closed", no reply
segment has RST, seq outside that window          -> IGNORED, state unchanged
```

## Reading Lens

The important move in this session is to stop treating RST as "one more flag" and start asking:

- did this segment even claim to be a reset? (`is_rst()` gates everything)
- was its sequence number inside the receiver's current window?
- what does "closed immediately" mean here — is there a reply, a wait, anything to negotiate?

## Toy Model Boundary

`on_reset()` implements RFC 5961's window check for accepting a RST, but not its challenge-ACK response for an in-window-but-unverified RST — the source comment says so directly: "RFC 5961 challenge-ACK behavior is out of scope here; we simply note the drop." A real stack receiving an out-of-window RST might still challenge the peer; this toy just ignores it and moves on. `new_state` is a bare string (`"Closed"`), not a `CloseState` member, so `on_reset()` does not participate in `teardown.py`'s enum at all — the two modules describe two different ways a connection ends, and only `speaker.py` reconciles the string back into `CloseState.CLOSED` for its own `state` field. `window` is clamped with `max(window, 1)` before the window check runs, so a caller that (incorrectly) passes a window of `0` still gets a one-byte window rather than a window check that rejects everything.

## Code Landmarks

### `on_reset()`'s first branch

`if not is_rst(segment): return ResetOutcome(NOT_A_RESET, state, ...)`. Every other branch can then assume the segment is a genuine reset — the function only has one flag to check to rule out "nothing to do here."

### `in_receive_window(segment.seq, rcv_nxt, max(window, 1))`

The acceptance test is delegated entirely to `seqnum.py`'s window arithmetic — `on_reset()` does not reimplement sequence comparison, it reuses the same function `reassembly.py` and the receive path use elsewhere in the track.

### The ACCEPTED branch

`CLOSED_STATE` — a module-level constant, not the `CloseState.CLOSED` enum member. `on_reset()` closes a connection without ever importing `teardown.py`. That separation is deliberate: this module has no notion of `FIN_WAIT_1` or `TIME_WAIT` to transition out of, because a RST from any state goes straight to closed.

### The IGNORED branch's docstring comment

"a real stack would send a challenge ACK" — the clearest single line in the module for naming exactly what the toy leaves out.

## Failure Questions

Use the source file to answer these:

1. `on_reset()` takes `rcv_nxt` and `window` as plain integers, not a `ReceiveBuffer`. What does a caller have to compute before calling this function, and where in `speaker.py` is that computation done?
2. Why does `on_reset()` check `is_rst(segment)` before checking anything about sequence numbers, rather than the other way around?
3. What is the type of `new_state` on the `ACCEPTED` branch, and how is that different from `new_state` on the `IGNORED` branch when `state` was originally a `CloseState` member?
4. If `window` is passed as `0`, does `in_receive_window()` see a window of `0` or something else? Which line in `on_reset()` decides?
5. A RST accepted from `CloseState.FIN_WAIT_1` and a FIN worked all the way through `teardown.py`'s four-packet path both eventually leave a connection with nothing left to negotiate. Read both `on_reset()`'s ACCEPTED branch and `time_wait_expired()`'s role in `teardown.py` — what does the RST path never produce that the FIN path always does?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tcp/session_10_walkthrough.py
```

The walkthrough sends an in-window RST into an `ESTABLISHED` connection and closes it with no reply, sends the identical RST again but now out of window and shows it `IGNORED`, sends a non-RST segment and shows `NOT_A_RESET`, and contrasts the RST's immediate `"Closed"` against `teardown.py`'s multi-step path to the same destination.

## Done When

The learner can say all of the following without looking at notes:

- "A RST only closes the connection if its sequence number lands inside the current receive window — otherwise it's noise."
- "RST has no reply and no wait: ACCEPTED goes straight to closed, nothing like TIME_WAIT exists on this path."
- "on_reset() and teardown.py never share an enum — reset.py's `new_state` is a plain string, and only speaker.py reconciles the two."

## References

- RFC 9293 Section 3.5.3 (Reset Processing)
