# Session 07 / Module 07: Streams Share One Connection

## Position

- Track: HTTP/QUIC
- Session: 07
- Site lesson: `pathvector-site/courses/protocols-in-code/http-quic/module-07/index.html`
- Source file: `src/protocol_in_code/http/h2_streams.py`
- Walkthrough script: `examples/http-quic/session_07_walkthrough.py`

## Core Question

An HTTP/2 connection multiplexes many independent request/response streams over one transport — what proves each stream's state is tracked separately, and what makes the very first frame on a stream special?

## Outcome

By the end of this session, the learner should be able to:

- name the four stream states this toy models and which real HTTP/2 states were dropped to get there
- explain why `DATA` cannot open a stream but `HEADERS` can
- trace `received` byte-counting across a HEADERS frame followed by a DATA frame
- explain why any frame arriving on a `HALF_CLOSED_REMOTE` stream closes it, rather than being treated as more data

## Read Order

1. Read the module-level comment citing RFC 9113 Section 5.1
2. Read `StreamState`
3. Read `FrameOutcome`
4. Read `Frame`
5. Read `Http2Connection`
6. Read `on_frame()`
7. Run `examples/http-quic/session_07_walkthrough.py`

## Read It Like Code

```python
Frame(
    stream_id,
    frame_type,
    payload_len,
    end_stream,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `stream_id` | Looks up (or defaults) this frame's stream state in `conn.streams`; every other stream is untouched by this call. |
| `frame_type` | Only `"HEADERS"` can open an `IDLE` stream; `"DATA"` on `IDLE` is an error regardless of `end_stream`. |
| `payload_len` | Added into `conn.received[stream_id]`, starting from the opening `HEADERS` frame itself, not just from the first `DATA` frame. |
| `end_stream` | The remote's signal that it is done sending; on `IDLE` or `OPEN` it moves the stream straight to `HALF_CLOSED_REMOTE`. |

## Decision Flow

```text
stream state == CLOSED                                    -> ErrorFrameAfterClosed
stream state == IDLE,  frame_type != "HEADERS"              -> ErrorDataOnIdleStream
stream state == IDLE,  frame_type == "HEADERS", end_stream    -> StreamHalfClosed (Idle -> HalfClosedRemote)
stream state == IDLE,  frame_type == "HEADERS", not end_stream -> StreamOpened    (Idle -> Open)
stream state == OPEN,  end_stream                             -> StreamHalfClosed (Open -> HalfClosedRemote)
stream state == OPEN,  not end_stream                          -> Accepted        (state unchanged)
stream state == HALF_CLOSED_REMOTE, any frame                  -> StreamClosed    (-> Closed)
```

## Reading Lens

The important move in this session is to stop reading `on_frame()` as one connection-wide state machine and start asking, on every call:

- which stream's state, specifically, does `conn.streams.get(frame.stream_id, StreamState.IDLE)` look up?
- does this call change `conn.streams[stream_id]`, and does it leave every other key in that dict untouched?
- is `payload_len` being added to an existing `received` total, or is it initializing one?

## Toy Model Boundary

Real RFC 9113 stream state includes `RESERVED_LOCAL` and `RESERVED_REMOTE` (for server push) and `HALF_CLOSED_LOCAL` (for when the local side, not the remote, has finished sending) — none of those exist here, because this connection only ever receives. There is no `RST_STREAM`, no stream priority, and no server push. Flow control — the `WINDOW_UPDATE` mechanics that actually bound how much data a sender is allowed to have in flight — is entirely absent from this toy; it is covered later, in the Session 09 file (`modules/http-quic/module-09-*.md`). Treat everything here as "does the frame arrive, and which of four states is the stream in," not "is the sender allowed to send it yet."

## Code Landmarks

### `StreamState` — the four kept, and why

`IDLE`, `OPEN`, `HALF_CLOSED_REMOTE`, `CLOSED`. Compare the module comment: this is the RFC 9113 Section 5.1 state diagram simplified to a "server-side, receive-only" toy, which is why every `HALF_CLOSED_LOCAL` and `RESERVED_*` transition in the real diagram has no counterpart here.

### `on_frame()` — the default lookup

`conn.streams.get(frame.stream_id, StreamState.IDLE)` — a stream that has never appeared in `conn.streams` is treated as `IDLE` without ever being written to the dict. The dict only gains an entry once a frame actually changes that stream's state.

### `on_frame()` — the IDLE branch

`if frame.frame_type != "HEADERS": return ERROR_DATA_ON_IDLE_STREAM` comes first, before `conn.received` is ever touched. Only after that guard does `conn.received[frame.stream_id] = frame.payload_len` run — note the plain assignment, not an increment, because this is the first frame on the stream.

### `on_frame()` — the OPEN branch's increment

`conn.received[frame.stream_id] = conn.received.get(frame.stream_id, 0) + frame.payload_len` — an increment, not an assignment, which is exactly what lets a HEADERS payload of 20 followed by a DATA payload of 30 sum to 50.

### `on_frame()` — the HALF_CLOSED_REMOTE fallthrough

The last branch of the function has no `if` guarding it — it is reached by process of elimination once `CLOSED`, `IDLE`, and `OPEN` have all been ruled out. Any `frame_type`, any `end_stream` value, on a `HALF_CLOSED_REMOTE` stream produces the same outcome: `STREAM_CLOSED`.

## Failure Questions

Use the source file to answer these:

1. `conn.received[frame.stream_id]` is set as a plain assignment in the `IDLE` branch but as `.get(..., 0) + payload_len` in the `OPEN` branch. Walk a HEADERS frame (payload_len=20) followed by a DATA frame (payload_len=30) on the same stream through both branches — what is `conn.received[stream_id]` after each, and which branch produced which value?
2. `on_frame()`'s `IDLE` branch returns `ERROR_DATA_ON_IDLE_STREAM` for any `frame_type` that is not `"HEADERS"` — not just `"DATA"`. Is there any `frame_type` string other than `"HEADERS"` and `"DATA"` that this code distinguishes, or does everything non-HEADERS collapse into the same error?
3. A stream that reaches `HALF_CLOSED_REMOTE` and then receives one more frame becomes `CLOSED` regardless of that frame's `end_stream` value or `frame_type`. Find the line that proves `end_stream` is never even read in that branch.
4. `conn.streams.get(frame.stream_id, StreamState.IDLE)` never writes `IDLE` into the dict. If you called `on_frame()` with a `DATA` frame on a brand-new `stream_id` and it returned `ERROR_DATA_ON_IDLE_STREAM`, would `conn.streams` contain that `stream_id` afterward? Check what the `IDLE` branch's error path does before returning.
5. Two different call sequences can both leave a stream in `HALF_CLOSED_REMOTE`: HEADERS with `end_stream=True` on a fresh stream, or HEADERS with `end_stream=False` followed later by a DATA frame with `end_stream=True`. Do both sequences produce the same `FrameOutcome` on the transitioning frame? What differs between the two paths in `conn.received`?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/http-quic/session_07_walkthrough.py
```

The walkthrough sends DATA on an idle stream first (error), opens stream 1 with HEADERS, interleaves a self-contained stream 3 while stream 1 is still OPEN (asserting both states independently), half-closes stream 1 with an end_stream DATA frame and checks the accumulated `received` total, then shows any further frame closing the stream outright and a frame after CLOSED erroring.

## Done When

The learner can say all of the following without looking at notes:

- "conn.streams is a dict because every stream's state is independent — advancing stream 3 never touches stream 1's entry."
- "Only HEADERS can open a stream; DATA arriving on an IDLE stream is always an error, never an implicit open."
- "HALF_CLOSED_REMOTE is not 'mostly done' — it's one frame away from CLOSED no matter what that next frame is."

## References

- RFC 9113 Section 5.1 (Stream States)
