# Session 04 / Module 04: The Window Is How Much Room You Have

## Position

- Track: TCP
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/tcp/module-04/index.html`
- Source file: `src/protocol_in_code/tcp/window.py`
- Walkthrough script: `examples/tcp/session_04_walkthrough.py`

## Core Question

What is the TCP receive window, really, and why is it never a number you store — only a number you compute?

## Outcome

By the end of this session, the learner should be able to:

- state the formula `advertised_window()` uses and name its two inputs
- explain why `ReceiveBuffer` has no `window` field of its own
- distinguish the three `AcceptOutcome`s and give a scenario that produces each
- explain what "reopens the window" means in terms of which field actually changes

## Read Order

1. Read `AcceptOutcome`
2. Read `ReceiveBuffer`
3. Read `advertised_window()`
4. Read `accept()`
5. Read `application_read()`
6. Run `examples/tcp/session_04_walkthrough.py`

## Read It Like Code

```python
ReceiveBuffer(
    capacity,
    buffered,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `capacity` | The total size of the receive buffer. Fixed for the buffer's lifetime in this toy. |
| `buffered` | How many bytes are currently sitting in the buffer, unread by the application. This is the only thing that changes; everything else is derived from it. |

Notice `window` is not a field here. `advertised_window()` is a function, not an attribute — the window is `capacity - buffered`, recomputed every time it's asked for, never cached anywhere.

## Decision Flow

```text
advertised_window(buffer)         -> max(0, capacity - buffered)

accept(buffer, payload_len):
  room = advertised_window(buffer)
  room <= 0                       -> Refused
  payload_len <= room             -> buffered += payload_len; Accepted
  otherwise                       -> buffered += room; Trimmed

application_read(buffer, n):
  freed = min(n, buffered)
  buffered -= freed
  return freed
```

## Reading Lens

The important move in this session is to stop thinking of "the window" as a value that gets set and start asking:

- what is `buffered` right now, and what does that make `advertised_window()` equal to?
- did this segment fit entirely, partially, or not at all against the *current* room?
- what changed `buffered` — an `accept()` call, or an `application_read()` call?

Every other question in this module reduces to tracking one integer, `buffered`, and recomputing `capacity - buffered` on demand.

## Toy Model Boundary

Real TCP receive windows interact with window scaling (RFC 9293's Section 3.8), silly window syndrome avoidance, and delayed-ACK timing that decides *when* a newly opened window gets advertised to the peer — none of that timing or scaling logic is here. `accept()` and `application_read()` are synchronous, local operations on one buffer; there's no peer to notify and no wire segment carrying the updated window value back out.

`accept()`'s `TRIMMED` outcome ("take what fits and drop the rest") is a simplification: real receivers generally don't silently accept a partial segment past the advertised window — a well-behaved sender should never send more than the window allows in the first place. This toy keeps `TRIMMED` as a defensive branch so the arithmetic (`room` vs `payload_len`) stays the reading target, not sender-compliance policy.

`ReceiveBuffer.capacity` never changes in this module — real buffer sizing (auto-tuning, memory pressure) is out of scope.

## Code Landmarks

### `ReceiveBuffer`

A plain (non-frozen) dataclass with exactly two fields. It is mutated in place by `accept()` and `application_read()` — unlike Session 01's `Segment`, this one is deliberately not frozen, because "how much is buffered" is state that changes over the buffer's lifetime.

### `advertised_window()`

One line: `max(0, capacity - buffered)`. The `max(0, ...)` matters — without it, a buffer that somehow held more than `capacity` would report a negative window, which is nonsensical as a window advertisement.

### `accept()`

The main reading target. Three outcomes, but read the order of the checks: room is computed once via `advertised_window()`, then reused for both the refuse-check and the fits-entirely-check. `TRIMMED` is the only branch where `payload_len` and the amount actually added to `buffered` (`room`) differ.

### `application_read()`

The window's only way back open. `freed = min(n, buffered)` means asking to read more than what's buffered is not an error — it just caps at whatever is actually there and reports how much was really freed.

## Failure Questions

Use the source file to answer these:

1. A buffer has `capacity=100, buffered=100`. What does `advertised_window()` return, and which branch of `accept()` handles the next `accept(buffer, 1)` call?
2. In the `TRIMMED` branch of `accept()`, how many bytes does `buffer.buffered` actually increase by — `payload_len`, or something else? Quote the line that decides it.
3. If `application_read(buffer, n)` is called with `n` larger than `buffer.buffered`, what does it return, and does `buffer.buffered` ever go negative?
4. Is there any code path in this file that sets `buffer.buffered` directly to a computed window value? What does that absence tell you about where "the window" actually lives?
5. At exactly `buffered == capacity`, is `advertised_window()` `0` or negative one step before `max()` is applied? Trace the arithmetic before the `max(0, ...)` wrapper.

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tcp/session_04_walkthrough.py
```

The walkthrough builds a 100-byte buffer, accepts segments until the window shrinks to zero and a refusal happens, then calls `application_read()` and shows the exact same buffer accepting more data — proving the window reopened purely because `buffered` went down.

## Done When

The learner can say all of the following without looking at notes:

- "The window is `capacity - buffered`, computed fresh every time — never a stored value that could drift out of sync."
- "`accept()` has three outcomes, and `TRIMMED` is the one where the bytes added and the bytes sent disagree."
- "The window only reopens because `application_read()` reduces `buffered` — there's no other lever."

## References

- RFC 9293 Section 3.8.6 (Managing the Window)
- RFC 9293 Section 3.4 (Sequence Numbers — the window's relationship to `rcv_nxt` from Session 03)
- RFC 9293 Section 3.1 (Header Format — the `window` field this session's buffer arithmetic ultimately fills in)
