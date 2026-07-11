# Session 08 / Module 08: QUIC Streams Don't Block Each Other

## Position

- Track: HTTP/QUIC
- Session: 08
- Site lesson: `pathvector-site/courses/protocols-in-code/http-quic/module-08/index.html`
- Source file: `src/protocol_in_code/quic/streams.py`
- Walkthrough script: `examples/http-quic/session_08_walkthrough.py`

## Core Question

TCP has one sequence space per connection, so a gap anywhere stalls everything behind it. QUIC gives every stream its own offset space — so what, mechanically, keeps one stream's gap from ever touching another stream's delivery?

## Outcome

By the end of this session, the learner should be able to:

- state why `QuicConnection` holds a `dict[int, StreamBuffer]` instead of one buffer
- trace a `deliver()` call for stream 8 and explain why it cannot affect stream 4's state
- explain why offset comparison here is plain `<`, not the modular `seq_lt()` from TCP
- reproduce, from the source alone, the exact scenario that proves streams are independent

## Read Order

1. Read the module comment above `DeliveryOutcome` (the two cross-references to `tcp/reassembly.py` and `tcp/seqnum.py`)
2. Read `StreamBuffer`
3. Read `QuicConnection`
4. Read `_buffer_for()`
5. Read `deliver()`
6. Run `examples/http-quic/session_08_walkthrough.py`

## Read It Like Code

```python
QuicConnection(
    streams,   # dict[int, StreamBuffer]: one buffer per stream_id, created on first use
)

StreamBuffer(
    rcv_offset,  # next offset expected on THIS stream, in order
    pending,     # dict[int, int]: offset -> length, gaps waiting on THIS stream
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `QuicConnection.streams` | The whole isolation mechanism lives here: a dict keyed by `stream_id`, not a single shared buffer. |
| `StreamBuffer.rcv_offset` | Scoped to one stream. Two different streams have two different `rcv_offset` values that never interact. |
| `StreamBuffer.pending` | A gap held here blocks only reads on this stream's `rcv_offset` — it is invisible to every other entry in `streams`. |

## Decision Flow

```text
length <= 0 or offset < buffer.rcv_offset   -> DUPLICATE   (0 bytes, rcv_offset unchanged)
offset != buffer.rcv_offset (there's a gap) -> BUFFERED    (stored in buffer.pending, rcv_offset unchanged)
offset == buffer.rcv_offset                 -> DELIVERED   (rcv_offset advances by length,
                                                              then drains every pending entry that is
                                                              now contiguous, one after another)
```

Note this is the exact three-way branch from TCP session 08's `deliver()` — the difference is which `buffer` gets passed in, chosen by `_buffer_for(conn, stream_id)` before any of this logic runs.

## Reading Lens

You saw this shape before, in TCP session 08 ("Out of Order Is Not Lost"): a `rcv_nxt`-like offset, a dict of pending out-of-order pieces, and a drain loop that fires when the gap closes. That module's `ReassemblyBuffer` is a single buffer for the whole connection — every byte on the wire, from any stream in the HTTP sense, shares one sequence space, so one gap stalls the entire connection's delivery.

This session's `StreamBuffer` is the same shape, but `QuicConnection.streams` holds one of them **per stream_id**. That one-line difference — a dict of buffers instead of one buffer — is the entire mechanism behind "HTTP/3 doesn't have head-of-line blocking at the transport layer." Read every `deliver()` call asking:

- which `StreamBuffer` does `_buffer_for()` return for this `stream_id` — is it new or does it already have state?
- does anything in `deliver()` ever read or write a `StreamBuffer` belonging to a different `stream_id`?
- if stream 8 is sitting on a gap, what does that predict about calling `deliver()` on stream 4 right now?

## Toy Model Boundary

This module models delivery *events* only — there are no QUIC packets, no frame headers (STREAM frames carry a stream ID, offset, and length, but this toy skips the framing entirely and hands `deliver()` those three fields directly), no ACKs, and no retransmission. A real QUIC stack must also decide *which* frames to retransmit after loss and must track packet-level acknowledgment separately from stream-level delivery; none of that exists here. `pending` stores only `offset -> length`, never actual bytes, exactly like TCP session 08's `segments`.

There is also no cap on the number of streams or on `pending`'s size — real QUIC enforces `MAX_STREAMS` and per-stream/connection flow-control limits (that's session 09) before a stream can even accept more buffered data.

## Code Landmarks

### The module comment above `DeliveryOutcome`

Two explicit cross-references worth reading before anything else: `tcp/reassembly.py` for the shape this file mirrors, and `tcp/seqnum.py` for why offset comparison changed. Both comments are the intended entry point into this file's design.

### `QuicConnection.streams` and `_buffer_for()`

`_buffer_for()` calls `conn.streams.setdefault(stream_id, StreamBuffer())` — a stream's buffer is created lazily, on first delivery, not up front. There is no step anywhere that pre-registers a stream; the first `deliver()` call for a `stream_id` is what brings it into existence.

### `deliver()`'s first condition

```python
if length <= 0 or offset < buffer.rcv_offset:
```

This is plain `<`, not `seq_lt()`. The comment above the class explains why: QUIC's offsets are 62-bit and, in practice, never wrap, so the ring-aware comparison TCP needs for its 32-bit sequence numbers is unnecessary machinery here.

### The drain loop

```python
while buffer.rcv_offset in buffer.pending:
    run_len = buffer.pending.pop(buffer.rcv_offset)
    delivered_len += run_len
    buffer.rcv_offset += run_len
```

Identical structure to TCP session 08's drain loop, operating on one stream's `pending` dict. A single `deliver()` call on the segment that closes the gap can return far more than the bytes it was handed — but only for that one stream.

## Failure Questions

Use the source file to answer these:

1. `_buffer_for()` uses `conn.streams.setdefault(stream_id, StreamBuffer())`. If `deliver()` is called for `stream_id=8` for the first time with an out-of-order `offset`, what is `StreamBuffer().rcv_offset` at the moment that first comparison runs?
2. Two calls to `deliver()`, one for `stream_id=4` and one for `stream_id=8`, both pass through the same `deliver()` function body. Which line is the only one that determines they operate on completely independent state?
3. The module comment says QUIC offsets "never wrap in practice." What line in `deliver()` would need to change if that assumption were false, and what TCP function would it need to import to fix it?
4. If `deliver(conn, stream_id=4, offset=0, length=12)` is called twice in a row with identical arguments, what outcome does the second call return, and which specific condition in `deliver()` catches it?
5. `StreamBuffer.pending` stores `offset -> length`. After a drain loop finishes consuming a contiguous run, are the drained entries still present in `pending` with stale data, or removed? Which method call in the loop is responsible?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/http-quic/session_08_walkthrough.py
```

The walkthrough delivers an in-order segment on stream 4, then buffers a gapped arrival on stream 8 (watching `rcv_offset` stay at 0), then delivers on stream 4 again to prove stream 8's gap never blocked it — the headline assertion — then fills stream 8's gap and watches one `deliver()` call drain its whole buffered run, then confirms a stale offset and a zero-length arrival both come back `DUPLICATE`.

## Done When

The learner can say all of the following without looking at notes:

- "QuicConnection keeps one StreamBuffer per stream_id; a gap on one stream cannot touch another stream's rcv_offset."
- "This is the same buffer shape TCP session 08 taught — the only structural change is the dict keyed by stream_id."
- "Offset comparison is plain `<` here because QUIC's 62-bit offsets don't wrap, unlike TCP's ring arithmetic."

## References

- RFC 9000 Section 2 (Streams)
