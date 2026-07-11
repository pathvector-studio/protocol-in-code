# Session 03 / Module 03: Sequence Numbers Wrap Around

## Position

- Track: TCP
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/tcp/module-03/index.html`
- Source file: `src/protocol_in_code/tcp/seqnum.py`
- Walkthrough script: `examples/tcp/session_03_walkthrough.py`

## Core Question

Sequence numbers are 32-bit and wrap back to zero — so what does "before" even mean once a connection has been running long enough to cross that boundary, and why is plain `<` the wrong tool to answer it?

## Outcome

By the end of this session, the learner should be able to:

- state `SEQ_SPACE` and explain why it is `2**32`, not `2**32 - 1`
- explain the signed-difference trick `seq_lt()` uses and why it only works because half the ring is defined as "ahead"
- give a concrete pair of sequence numbers where plain `<` and `seq_lt()` disagree
- explain what `in_receive_window()` checks and why it needs both `rcv_nxt` and `window`

## Read Order

1. Read `SEQ_SPACE`
2. Read `seq_add()`
3. Read `seq_lt()`
4. Read `seq_le()`
5. Read `in_receive_window()`
6. Run `examples/tcp/session_03_walkthrough.py`

## Read It Like Code

```python
seq_lt(a, b)   # is a "before" b on the ring?
seq_le(a, b)   # a == b or seq_lt(a, b)
in_receive_window(seq, rcv_nxt, window)  # does seq fall in [rcv_nxt, rcv_nxt + window)?
```

## Fields That Matter

There are no dataclasses in this module — every function in `seqnum.py` takes plain integers. That absence is the point: this session is about arithmetic on a ring, not about a structure to inspect.

| Name | Why it matters |
|---|---|
| `SEQ_SPACE` | `2**32`. The modulus every function in this module reduces against. |
| `a`, `b` (in `seq_lt`/`seq_le`) | Two raw sequence numbers, each already in `[0, SEQ_SPACE)`. Neither is privileged as "current" — the function just orders them. |
| `rcv_nxt`, `window` (in `in_receive_window`) | Together they define the acceptable range `[rcv_nxt, rcv_nxt + window)`, which itself may wrap past `SEQ_SPACE`. |

## Decision Flow

```text
seq_add(a, n)              -> (a + n) % SEQ_SPACE

seq_lt(a, b):
  (b - a) % SEQ_SPACE < SEQ_SPACE // 2  and  a != b   -> True
  otherwise                                            -> False

seq_le(a, b):
  a == b  or  seq_lt(a, b)                             -> True
  otherwise                                             -> False

in_receive_window(seq, rcv_nxt, window):
  window <= 0                        -> seq == rcv_nxt
  otherwise: offset = (seq - rcv_nxt) % SEQ_SPACE
             offset < window          -> True
```

## Reading Lens

The important move in this session is to stop thinking "sequence numbers are just big integers, so I can compare them with `<`" and start asking:

- how far apart are these two numbers going *forward* around the ring, not by subtraction in the ordinary sense?
- is that forward distance less than half the ring? That's what "ahead" means here.
- for `in_receive_window()`: does the *offset* from `rcv_nxt` fall inside `window`, treating the whole check as a distance-and-wrap problem, not a min/max range check?

`seq_lt(a, b)` is not "a's numeric value is smaller." It is "walking forward from a, you reach b before you've gone halfway around the ring." That reframing is the entire session.

## Toy Model Boundary

Real TCP sequence-number comparisons (RFC 9293 uses the term "sequence number arithmetic modulo 2**32") also have to account for retransmission ambiguity, PAWS (Protection Against Wrapped Sequences) using timestamps, and ISN randomization to defend against blind spoofing. This module skips all of that: it implements exactly the ring arithmetic needed to answer "is a before b" and "is seq in the acceptable receive range," nothing about how those functions get used to defend a real connection.

`seq_lt()`'s half-the-ring rule breaks down if the true distance between two sequence numbers is close to or exceeds `SEQ_SPACE // 2` — real implementations avoid this by keeping window sizes far smaller than half the sequence space. This module does not enforce that constraint; it is a property the caller must respect for the comparison to mean anything.

## Code Landmarks

### `SEQ_SPACE`

`2**32`, matching the 32-bit sequence number field from Session 01's `Segment.seq`. Every other function in this file reduces modulo this constant.

### `seq_add()`

The simplest function here, and the one that makes wrapping concrete: adding past `SEQ_SPACE - 1` lands back near zero.

### `seq_lt()`

The main reading target. `(b - a) % SEQ_SPACE < SEQ_SPACE // 2` computes the forward distance from `a` to `b` and asks if it's in the "near" half of the ring. The `and a != b` guard is what makes a value never "less than" itself — without it, `(b - a) % SEQ_SPACE` for `a == b` is `0`, which is less than half the ring, and the function would wrongly say a number is before itself.

### `seq_le()`

Built entirely from `seq_lt()` plus an equality check — no independent ring arithmetic of its own.

### `in_receive_window()`

Two branches. `window <= 0` collapses the acceptable range to exactly one value, `rcv_nxt` itself — this is the zero-window case that Session 04's `advertised_window()` can produce. Otherwise, `offset = (seq - rcv_nxt) % SEQ_SPACE` turns the wraparound range check into a plain `offset < window` comparison.

## Failure Questions

Use the source file to answer these:

1. For `a = 2**32 - 1` and `b = 0`, what does `seq_lt(a, b)` return? What would plain integer `<` return for the same two values, and why do they disagree?
2. Why does `seq_lt(a, a)` return `False` for every `a`? Which specific piece of the expression makes that guaranteed rather than incidental?
3. At exactly `seq == rcv_nxt + window` (not one less), does `in_receive_window()` return `True` or `False`? Trace the `offset < window` comparison to be sure.
4. When `window == 0`, what is the only `seq` value `in_receive_window()` accepts? Which branch decides this, and why does it not fall through to the offset computation?
5. Is `seq_le(a, b)` ever `True` when `seq_lt(a, b)` is `False` and `a != b`? Read the definition of `seq_le()` to justify your answer.

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tcp/session_03_walkthrough.py
```

The walkthrough picks a sequence number 10 below the top of the ring, adds past the wrap, and shows a case where plain `<` gives the wrong answer but `seq_lt()` gives the right one — then extends the same idea to `seq_le()` and to a receive window that spans the wrap.

## Done When

The learner can say all of the following without looking at notes:

- "Sequence numbers live on a ring of size 2**32; 'before' means forward-distance-within-half-the-ring, not numeric less-than."
- "Plain `<` is wrong exactly when the comparison straddles the wrap point — `seq_lt()` is the only correct tool near 2**32 -> 0."
- "A receive window is a range starting at `rcv_nxt`, and that range itself can wrap, which is why `in_receive_window()` works in offsets, not absolute bounds."

## References

- RFC 9293 Section 3.4 (Sequence Numbers)
- RFC 9293 Section 3.4.1 (specifically the "Sequence Number Wraparound" discussion of modulo-2**32 arithmetic)
- RFC 9293 Section 3.8.6 (Managing the Window — the receive-window range `in_receive_window()` implements)
