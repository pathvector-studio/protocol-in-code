# Session 06 / Module 06: Three Duplicates Mean Loss

## Position

- Track: TCP
- Session: 06
- Site lesson: `pathvector-site/courses/protocols-in-code/tcp/module-06/index.html`
- Source file: `src/protocol_in_code/tcp/fast_retransmit.py`
- Walkthrough script: `examples/tcp/session_06_walkthrough.py`

## Core Question

How does a sender infer a lost segment from ACKs alone, without waiting for a retransmission timer to expire?

## Outcome

By the end of this session, the learner should be able to:

- explain what a "duplicate ACK" is in terms of the value carried, not just that it repeats
- state exactly which repeat count flips the signal to fast retransmit
- explain why a fourth repeat of the same ack is not a second fast-retransmit trigger
- explain what resets the duplicate counter, and why that's the same event as "new data acked"

## Read Order

1. Read `DUP_ACK_THRESHOLD`
2. Read `AckSignal`
3. Read `AckTracker`
4. Read `on_ack()`
5. Run `examples/tcp/session_06_walkthrough.py`

## Read It Like Code

```python
AckTracker(
    last_ack,
    dup_count,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `last_ack` | The most recently seen ack value. Every incoming ack is compared against this, not against "the highest ack ever seen" or any window state. |
| `dup_count` | How many times *in a row* the current `last_ack` has repeated. Any new ack value resets this to zero. |

## Decision Flow

```text
ack != tracker.last_ack        -> NEW_DATA_ACKED  (last_ack updates, dup_count resets to 0)
ack == tracker.last_ack:
    dup_count += 1
    dup_count == DUP_ACK_THRESHOLD (3)  -> FAST_RETRANSMIT
    otherwise                            -> DUPLICATE
```

## Reading Lens

The important move in this session is to stop thinking "three duplicate ACKs means loss" as a vague rule of thumb, and start asking:

- is this comparison `==` or `>=`? (It changes what happens on the fourth, fifth, sixth repeat.)
- what exact value does `dup_count` hold at the moment `FAST_RETRANSMIT` is returned?
- does a repeat of the ack *before* the current `last_ack` count toward anything, or is it just compared to `last_ack`?
- what is the very next `AckSignal` after `FAST_RETRANSMIT`, if the same ack repeats again?

## Toy Model Boundary

Real TCP receivers with Selective Acknowledgment (SACK, RFC 2018) tell the sender exactly which blocks of data have arrived, so a sender doesn't have to guess from a single repeated cumulative ack which segment is missing — it can often identify and retransmit just the missing piece immediately. This toy has no SACK: `on_ack()` only ever sees a single integer `ack` value and counts exact repeats. It cannot tell three duplicate acks apart from "receiver is acking three different segments that all still expect the same next byte" versus "three separate small losses" — it just counts.

There's also no notion of an ACK carrying window or timestamp information here, and no interaction with the RTO timer from Session 05 — `AckTracker` is a pure counter over a stream of ack values, nothing more.

## Code Landmarks

### `DUP_ACK_THRESHOLD = 3`

A single module-level constant. Every "why three?" question in TCP folklore collapses to this one number being read once, in one comparison.

### `AckSignal`

Three outcomes, no more. There is no "still waiting" or "unknown" — every call to `on_ack()` returns exactly one of these three.

### `on_ack()`

The reading target, and it's short enough to read as one unit. The `!=` branch is the reset path — it runs before `dup_count` is ever touched for this ack. The literal `== DUP_ACK_THRESHOLD` comparison (not `>=`) is what makes fast retransmit a one-time edge, not a level: the third repeat trips it, and the fourth repeat, still equal to `last_ack`, increments `dup_count` to 4 and falls through to `DUPLICATE` because `4 != 3`.

## Failure Questions

Use the source file to answer these:

1. At exactly the third duplicate of the same ack, what does `on_ack()` return, and what is `tracker.dup_count` immediately after that call?
2. If the same ack repeats a fourth time after triggering `FAST_RETRANSMIT`, what does `on_ack()` return this time? Which line explains why it isn't `FAST_RETRANSMIT` again?
3. An ack repeats twice (`dup_count` reaches 2), then a genuinely new ack value arrives. What does `on_ack()` return, and what are `last_ack` and `dup_count` afterward?
4. `AckTracker()` defaults `last_ack` to `0`. If the very first real ack a sender ever sees also happens to be `0`, what does `on_ack()` return, and why does the field's default value matter here?
5. If `DUP_ACK_THRESHOLD` were changed to `1`, what would `on_ack()` return on the very first duplicate, and which line's comparison would make that true?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tcp/session_06_walkthrough.py
```

The walkthrough sends one ack, repeats it three times to watch `DUPLICATE, DUPLICATE, FAST_RETRANSMIT`, repeats it a fourth time to show the signal falls back to `DUPLICATE`, then sends new data to show the counter resets and a fresh duplicate run starts from 1.

## Done When

The learner can say all of the following without looking at notes:

- "Three duplicates of the *same* ack value trip fast retransmit — the third one exactly, via `==`, not `>=`."
- "A fourth repeat is not a second fast-retransmit signal; it's just another duplicate."
- "Any ack value different from `last_ack` resets `dup_count` to zero — that's the same branch that reports `NEW_DATA_ACKED`."

## References

- RFC 5681 Section 3.2 (fast retransmit / fast recovery)
