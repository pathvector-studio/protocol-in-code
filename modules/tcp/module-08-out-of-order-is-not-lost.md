# Session 08 / Module 08: Out of Order Is Not Lost

## Position

- Track: TCP
- Session: 08
- Site lesson: `pathvector-site/courses/protocols-in-code/tcp/module-08/index.html`
- Source file: `src/protocol_in_code/tcp/reassembly.py`
- Walkthrough script: `examples/tcp/session_08_walkthrough.py`

## Core Question

When a segment arrives ahead of where the receiver expects, what actually happens to it, and what makes the receiver able to catch up in one step once the gap closes?

## Outcome

By the end of this session, the learner should be able to:

- state the three possible outcomes of `deliver()` and which comparison decides between them
- explain why an out-of-order segment doesn't move `rcv_nxt` at all
- trace exactly how a single `deliver()` call can hand back far more than the bytes it was called with
- explain why a duplicate (already-seen) segment and a zero-length segment produce the same outcome

## Read Order

1. Read `DeliveryOutcome`
2. Read `DeliveryResult`
3. Read `ReassemblyBuffer`
4. Read `seq_lt()` in `seqnum.py` (used by `deliver()`)
5. Read `deliver()`
6. Run `examples/tcp/session_08_walkthrough.py`

## Read It Like Code

```python
ReassemblyBuffer(
    rcv_nxt,
    segments,   # dict[int, int]: seq -> payload_len, everything not yet contiguous with rcv_nxt
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `rcv_nxt` | The next sequence number the receiver expects, in order. This is the only pointer into "how much has been delivered." |
| `segments` | A holding area keyed by starting sequence number. A segment sits here exactly as long as there's a gap between `rcv_nxt` and its `seq`. |

## Decision Flow

```text
payload_len <= 0 or seq is before rcv_nxt   -> DUPLICATE   (0 bytes, rcv_nxt unchanged)
seq != rcv_nxt (there's a gap)              -> BUFFERED    (stored in segments, rcv_nxt unchanged)
seq == rcv_nxt (lands exactly at the edge)  -> DELIVERED   (rcv_nxt advances by payload_len,
                                                             then drains every segment that is now
                                                             contiguous, one after another)
```

## Reading Lens

The important move in this session is to stop picturing reassembly as "sort all the segments, then read them off in order," and instead ask, for each `deliver()` call:

- is `seq` before `rcv_nxt`, equal to it, or after it — and which of those three is being tested first?
- when a segment lands exactly at `rcv_nxt`, does the function stop after advancing past it, or does it keep looking?
- what does `buffer.segments` look like right before the drain loop starts, and right after it ends?
- does `delivered_len` in the result ever exceed the `payload_len` the caller passed in? When, and why?

## Toy Model Boundary

Real TCP receivers with SACK (RFC 2018) report the buffered-but-not-yet-contiguous ranges back to the sender, so the sender knows precisely what's missing instead of just re-sending everything from `rcv_nxt` forward. This toy has no SACK generation at all — `deliver()` only tracks what the *receiver* has buffered locally; it never produces anything to tell a sender about it.

`ReassemblyBuffer.segments` also stores only `seq -> payload_len`, never the actual bytes. This toy is entirely about the bookkeeping of *which* ranges have arrived and when they become contiguous — it has no byte storage, no overlap-trimming of partially-overlapping segments, and no receive-window enforcement (that lives in `seqnum.in_receive_window()`, which `deliver()` doesn't call at all).

## Code Landmarks

### `DeliveryOutcome` / `DeliveryResult`

Three outcomes, and `DeliveryResult` is frozen — a `deliver()` call cannot mutate a result after returning it. `delivered_len` and `new_rcv_nxt` are meaningful only when `outcome is DELIVERED`; both are `0` / `buffer.rcv_nxt` unchanged otherwise, but that "unchanged" value is still populated (never `None`), so callers don't need special-case handling for the other two outcomes.

### `seq_lt()` (from `seqnum.py`)

`deliver()`'s very first check, `seq_lt(seq, buffer.rcv_nxt)`, relies on this ring-aware comparison rather than plain `<`, so a stale segment is correctly recognized as stale even across a sequence-number wraparound. Read this alongside Session 08's `deliver()`, not in isolation.

### `deliver()`

The reading target, and specifically its drain loop:

```python
while buffer.rcv_nxt in buffer.segments:
    run_len = buffer.segments.pop(buffer.rcv_nxt)
    delivered_len += run_len
    buffer.rcv_nxt = seq_add(buffer.rcv_nxt, run_len)
```

This is what lets one `deliver()` call — the one that finally fills the gap — return far more than the bytes it was handed. Each iteration checks the dictionary for the *new* `rcv_nxt`, so any chain of previously-buffered, now-contiguous segments gets consumed in a single call, not one call per segment.

## Failure Questions

Use the source file to answer these:

1. A segment arrives with `seq` equal to `buffer.rcv_nxt` exactly. Which branch handles it, and does the function check `seq != buffer.rcv_nxt` or `seq == buffer.rcv_nxt` to route it there?
2. Three segments arrive out of order — first the last one, then the middle one, then the one that fills the initial gap. How many of those three `deliver()` calls return `DELIVERED`, and what is `delivered_len` on that call?
3. A segment with `payload_len = 0` arrives at exactly `seq == buffer.rcv_nxt`. Does it get treated as `DELIVERED` or `DUPLICATE`? Which line decides this before `seq` is ever compared to `rcv_nxt`?
4. After a gap-filling `deliver()` call drains a run of buffered segments, what is left in `buffer.segments` for the segments that were just drained — are they deleted, or merely marked as consumed?
5. If a segment arrives with the same `seq` as one already sitting in `buffer.segments` (not yet drained), what happens to the stored `payload_len` for that `seq`? Which line in `deliver()` is responsible?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tcp/session_08_walkthrough.py
```

The walkthrough delivers one in-order segment, then buffers two out-of-order segments (watching `rcv_nxt` stay put both times), then sends the one segment that closes the gap and watches a single `deliver()` call drain all three segments' worth of bytes at once, then confirms a stale segment and a zero-length segment both come back `DUPLICATE`.

## Done When

The learner can say all of the following without looking at notes:

- "An out-of-order segment is buffered by sequence number; `rcv_nxt` does not move until the gap closes."
- "The segment that finally lands at `rcv_nxt` can trigger a drain loop that delivers everything contiguous after it, all in one call."
- "`DUPLICATE` covers both 'this data already arrived' and 'this segment has no bytes at all' — one check handles both."

## References

- RFC 9293 Section 3.4 (sequence numbers: arithmetic, comparison, and the ring model that `seq_lt()` implements)
