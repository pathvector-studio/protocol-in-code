# Session 03 / Module 03: Nagle and Delayed ACK Deadlock

## Position

- Track: TCP2
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/tcp2/module-03/index.html`
- Source file: `src/protocol_in_code/tcp2/nagle_delack.py`
- Walkthrough script: `examples/tcp2/session_03_walkthrough.py`

## Core Question

Nagle's algorithm and delayed ACK are each a reasonable optimization on their own. Run them together against the same write pattern, and where does the 200ms stall actually come from?

## Outcome

By the end of this session, the learner should be able to:

- trace a write-write-read sequence and say exactly which side is holding what, and why
- explain why `TCP_NODELAY` (the `nodelay` flag) breaks the standoff by acting on the sender, not the receiver
- explain why a lone write-read pattern already stalls 200ms even with nothing for Nagle to hold
- read the `events` tuple and say who released whom, and when

## Read Order

1. Read the module docstring on `READ` as a sentinel
2. Read `DELACK_TIMEOUT_MS`
3. Read `Timeline`
4. Read `simulate()`'s docstring in full
5. Read the `READ` branch of `simulate()`
6. Read the write branch of `simulate()`
7. Run `examples/tcp2/session_03_walkthrough.py`

## Read It Like Code

```python
Timeline(
    events,
    total_ms,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `events` | An ordered trace of every hold, send, and release — the whole story of who was waiting for whom. |
| `total_ms` | The clock value when the simulated read completes. `0` means no stall; `DELACK_TIMEOUT_MS` (200) means the timer had to fire. |
| `unacked_segment` (local var) | True while the sender has one segment out with no ACK — this is what makes Nagle hold the next small write. |
| `pending_ack` (local var) | True while the receiver is sitting on an ACK, hoping a second segment arrives to piggyback on. |

## Decision Flow

```text
on a write:
  unacked_segment and not nodelay  -> Nagle holds this write (held_write = write_len)
  otherwise                        -> send the segment now, unacked_segment = True
        if pending_ack already set -> second segment lets receiver ack immediately (piggyback)
        else                       -> pending_ack = True (receiver starts its own wait)

on a READ:
  pending_ack still set  -> delayed-ack timer fires (+200ms), release any held_write
  application read completes at the current clock
```

## Reading Lens

Session 09 of Track 1 modeled a connection's close as arithmetic on `entered_at + TWO_MSL` — a single wait, one side, one clock. This session is two independent waits, on two different sides, each individually reasonable, that end up waiting on each other:

- at the moment of the stall, is the *sender* holding something, or the *receiver*, or both?
- if you only look at Nagle, does the code ever get stuck? If you only look at delayed ACK, does it?
- which single flag flips, and which side of the connection does it act on — sender or receiver?

The move is to resist collapsing this into "Nagle and delack are bad together" and instead trace exactly which held thing was waiting on which other held thing.

## Toy Model Boundary

`DELACK_TIMEOUT_MS` is a fixed 200ms constant here. Real delayed-ACK implementations are adaptive and interact with the estimated RTT, and some stacks cap the delay lower under fast local RTTs — this file keeps it a bare constant so the stall duration in every scenario is exact and predictable. This file also models exactly one unacked segment and one held write at a time; it does not model a stream of many small writes queueing up behind Nagle, nor does it model the receiver's ACK being lost and needing retransmission. `nodelay` here is a single boolean the caller sets per-simulation; a real socket toggles `TCP_NODELAY` mid-connection, and this file does not model a state change partway through a `writes` sequence.

## Code Landmarks

### The `READ` sentinel

`READ = -1`. The docstring's reasoning: instead of adding a second parameter to distinguish writes from reads, one sentinel value lets `writes: tuple[int, ...]` stay a single flat tuple, so a pattern like "write, write, then block for a reply" is literally `(10, 20, READ)`.

### `simulate()`'s write branch

The Nagle decision is one condition: `unacked_segment and not nodelay`. Note what is absent — there is no check of how *small* the write is. In this toy, "in flight" alone is enough to hold the next write; the real algorithm's small-vs-full-segment distinction is not modeled.

### `simulate()`'s `READ` branch

The delayed-ACK timeout only fires here, inside the `pending_ack` check — nothing about a write ever advances the clock on its own. `clock_ms += DELACK_TIMEOUT_MS` is the only place `clock_ms` moves in the entire function.

### The deadlock, read as two waits

Comment in the source, `READ` branch: the sender's held write is stuck behind Nagle waiting for the very ACK the receiver is sitting on, and the receiver won't send that ACK without a second segment — which is the held write. Each side is correctly waiting for the other; neither is broken on its own.

## Failure Questions

Use the source file to answer these:

1. In the write-write-read scenario with `nodelay=False`, which event in `events` names the exact thing releasing the held write — and what has to happen first for that release to fire?
2. `simulate()` only advances `clock_ms` in one place. Which branch, and what is added to it?
3. Setting `nodelay=True` changes the outcome of the write-write-read scenario to `total_ms == 0`. Which side does `nodelay` act on — sender or receiver — and which condition in the write branch does it change?
4. A single write followed by a read (no second write at all) still produces `total_ms == 200` in the walkthrough. Since there is no second write for Nagle to hold, what is the source of that 200ms stall?
5. In the write-write-read case, `pending_ack` is checked before `unacked_segment` is ever reset back to `False`. Trace the order: which local variable gets reset first inside the timeout branch, `pending_ack` or `unacked_segment`, and does the order matter to the outcome?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tcp2/session_03_walkthrough.py
```

The walkthrough drives write-write-read with Nagle and delayed ACK both active and asserts `total_ms == 200`, checking the exact held-write and timeout-fired events in the trace; repeats the same writes with `nodelay=True` and asserts `total_ms == 0` with the immediate-piggyback event present; and runs a single write-read to show the pattern still stalls 200ms on delayed ACK alone, with no held-write event anywhere in its trace — proof the 200ms in that case is not a Nagle problem at all.

## Done When

The learner can say all of the following without looking at notes:

- "Nagle holds the second write because the first is still unacked; delayed ACK holds the ACK because only one segment has arrived. Each side is waiting on the other."
- "TCP_NODELAY fixes this by acting on the sender — it stops the hold, so the receiver gets a second segment to piggyback on and never needs its timer."
- "A single write-read stalls 200ms too, with nothing held by Nagle at all — delayed ACK alone is enough to cause that wait."

## References

- RFC 896 (Congestion Control in IP/TCP Internetworks — the original statement of Nagle's algorithm)
- RFC 1122 Section 4.2.3.2 (delayed acknowledgments)
