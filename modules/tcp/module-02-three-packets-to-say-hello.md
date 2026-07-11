# Session 02 / Module 02: It Takes Three Packets to Say Hello

## Position

- Track: TCP
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/tcp/module-02/index.html`
- Source file: `src/protocol_in_code/tcp/handshake.py`
- Walkthrough script: `examples/tcp/session_02_walkthrough.py`

## Core Question

Why does establishing a connection take exactly three segments, and what state is each side in after each one?

## Outcome

By the end of this session, the learner should be able to:

- name the five states in `ConnectionState` and which ones are transient
- trace the client's path: `CLOSED -> SYN_SENT -> ESTABLISHED`
- trace the server's path: `LISTEN -> SYN_RCVD -> ESTABLISHED`
- explain why the final ACK carries no reply segment at all

## Read Order

1. Read `ConnectionState`
2. Read `HandshakeStep`
3. Read `active_open()`
4. Read `on_segment()`, the `LISTEN` branch
5. Read `on_segment()`, the `SYN_RCVD` branch
6. Read `on_segment()`, the `SYN_SENT` branch
7. Run `examples/tcp/session_02_walkthrough.py`

## Read It Like Code

```python
HandshakeStep(
    new_state,
    reply,
    note,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `new_state` | Where the connection lands after processing this one segment. Often the same as the state that came in. |
| `reply` | The segment to send back, or `None` if nothing needs to go out. The final ACK produces `reply=None` on the server side — the handshake just ends. |
| `note` | A one-line explanation of why this transition happened. Not protocol data — it exists so the walkthrough (and you) can narrate the trace. |

## Decision Flow

```text
state = LISTEN,     segment has SYN            -> SYN_RCVD, send SYN+ACK
state = LISTEN,     segment lacks SYN          -> LISTEN, nothing to send

state = SYN_RCVD,   segment has ACK, no SYN    -> ESTABLISHED, nothing to send
state = SYN_RCVD,   otherwise                  -> SYN_RCVD, still waiting

state = SYN_SENT,   segment has SYN and ACK    -> ESTABLISHED, send final ACK
state = SYN_SENT,   segment has SYN only       -> SYN_SENT, ignored (simultaneous open)
state = SYN_SENT,   otherwise                  -> SYN_SENT, still waiting

state = ESTABLISHED                            -> ESTABLISHED, nothing to negotiate
state = CLOSED (fallthrough)                   -> unchanged, nothing to negotiate
```

## Reading Lens

The important move in this session is to stop thinking of the handshake as "SYN, SYN-ACK, ACK" as three interchangeable steps and start asking, for each segment:

- what state was this side in *before* the segment arrived?
- what does the reply's `seq` and `ack` say about what was just acknowledged?
- did this transition produce a segment to send, or just an internal state change?

The third segment is the one worth sitting with: it advances the server to `ESTABLISHED`, and `HandshakeStep.reply` is `None`. The handshake completing is a state change with no wire traffic of its own.

## Toy Model Boundary

Real TCP negotiates MSS, window scaling, and SACK-permitted options inside the SYN and SYN+ACK segments, and initial sequence numbers are chosen with anti-spoofing randomness, not passed in as a plain `iss` argument. This toy accepts `iss` as a parameter so every scenario in the walkthrough is reproducible — no clock, no randomness.

`on_segment()` explicitly acknowledges simultaneous open (`SYN_SENT` receiving a bare SYN) only to say the toy ignores it — the comment calls this out as "not this course's focus." There is no code path here for the four-segment simultaneous-open handshake from RFC 9293.

Retransmission, timeouts, and the `SYN_SENT` retry logic if a SYN is lost are entirely out of scope — every scenario in this session assumes segments arrive, in order, exactly once.

## Code Landmarks

### `ConnectionState`

Five states. `CLOSED` and `LISTEN` are where a side starts; `SYN_SENT` and `SYN_RCVD` are transient, existing only until the next expected segment arrives; `ESTABLISHED` is where the handshake's job ends.

### `active_open()`

The client's only move: build a bare SYN carrying its own `iss` as `seq`, move to `SYN_SENT`, and wait. No `ack` is meaningful yet — the client hasn't heard from the server.

### `on_segment()`, `LISTEN` branch

A listener does nothing until it hears a SYN. When it does, the reply's `ack` is `segment.seq + 1` — the first concrete evidence in this codebase that "ack" means "next byte I expect," not "the byte I just got."

### `on_segment()`, `SYN_SENT` branch

Look closely at the difference between "SYN and ACK both present" (advance to `ESTABLISHED`, reply with the final ACK) versus "SYN only" (simultaneous open, explicitly ignored). The final ACK's `seq` is `segment.ack` — the client sends back exactly the sequence number the server told it to expect next.

## Failure Questions

Use the source file to answer these:

1. A server in `SYN_RCVD` receives a segment with both SYN and ACK set. Which branch handles it, and what state does the server end up in?
2. What is `final_ack.ack` in terms of the SYN+ACK segment's fields? Read the `SYN_SENT` branch to derive the exact expression.
3. If a client in `SYN_SENT` receives a bare SYN (no ACK), what does `on_segment()` return, and what does the `note` field say about why?
4. Once a connection reaches `ESTABLISHED`, what does `on_segment()` return for any further segment, regardless of its flags?
5. Trace `on_segment()` for `state=CLOSED` with any segment. Which branch handles it, and what is `new_state`?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tcp/session_02_walkthrough.py
```

The walkthrough drives both sides of a handshake — client `active_open()`, then alternating `on_segment()` calls for server and client — counts the segments that actually went on the wire, and confirms both sides land on `ESTABLISHED` after exactly three.

## Done When

The learner can say all of the following without looking at notes:

- "The client and server each have their own three-state path, and they only agree on `ESTABLISHED` at the very end."
- "The handshake takes exactly three segments: SYN, SYN+ACK, ACK — the third produces no reply of its own."
- "`ack` in each segment is always 'next byte I expect,' computed as the peer's `seq` plus one."

## References

- RFC 9293 Section 3.3 (Connection State Diagram — the five states this session models a subset of)
- RFC 9293 Section 3.5 (Establishing a Connection — the three-way handshake itself)
- RFC 9293 Section 3.4 (Sequence Numbers — why `ack = seq + 1` for a control segment)
