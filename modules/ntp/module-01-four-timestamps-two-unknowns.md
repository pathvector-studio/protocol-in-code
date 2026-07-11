# Session 01 / Module 01: Four Timestamps, Two Unknowns

## Position

- Track: NTP
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/ntp/module-01/index.html`
- Source file: `src/protocol_in_code/ntp/offset.py`
- Walkthrough script: `examples/ntp/session_01_walkthrough.py`

## Core Question

An NTP exchange hands back four timestamps. What can you actually solve for from just those four numbers, and what has to be assumed to get there?

## Outcome

By the end of this session, the learner should be able to:

- name all four timestamps and what event each one marks
- derive `offset()` and `delay()` from the two equations in the module docstring, not just quote the formulas
- say which assumption makes two equations with three unknowns solvable
- explain why `validate_exchange()` checks `t4 < t1` and `t3 < t2` and nothing else

## Read Order

1. Read the module docstring's derivation top to bottom
2. Read `Exchange`
3. Read `validate_exchange()`
4. Read `offset()`
5. Read `delay()`
6. Run `examples/ntp/session_01_walkthrough.py`

## Read It Like Code

```python
Exchange(
    t1,  # client transmit time
    t2,  # server receive time
    t3,  # server transmit time
    t4,  # client receive time
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `t1` | When the client sent the request, by the client's own clock. |
| `t2` | When the server received it, by the server's clock -- the first timestamp that can carry clock offset. |
| `t3` | When the server sent the reply, by the server's clock. |
| `t4` | When the client received the reply, by the client's own clock again. |

## Decision Flow

```text
t4 < t1  or  t3 < t2   -> Malformed  (not one coherent round trip)
otherwise              -> Valid     (offset() and delay() are trustworthy)
```

## Reading Lens

The important move in this session is to stop treating `offset()` and `delay()` as formulas to memorize and start asking:

- which of the four timestamps came from the client's clock, and which from the server's?
- in the docstring's two equations (`t2 = t1 + d_out + theta`, `t4 = t3 + d_in - theta`), which term is the thing NTP actually wants (`theta`), and which two terms does it have to get rid of to isolate it?
- what happens to those equations if you add them versus subtract them?

## Toy Model Boundary

Real NTP timestamps are 64-bit fixed-point values in the NTP era format (seconds since 1900, with a fractional part good to about 232 picoseconds). This toy uses plain integer milliseconds -- `Exchange`'s own docstring says so directly -- so the arithmetic reads like arithmetic instead of like bit-shifting. There is no era rollover, no fractional precision, and no NTP header (no leap indicator, no version, no mode) here at all; this module is only the four-timestamp math from RFC 5905 section 8, nothing upstream or downstream of it.

## Code Landmarks

### The module docstring's derivation

This is the actual lesson, not decoration. `t2 = t1 + d_out + theta` says the server's receive timestamp is the client's send time, plus how long the packet took to arrive, plus however far the server's clock reads ahead of the client's. `t4 = t3 + d_in - theta` is the mirror image for the return trip -- note the sign flip on `theta`, because now it's the client's clock reading behind by the same amount it read ahead of on the way out. Two equations, three unknowns (`d_out`, `d_in`, `theta`) -- until symmetry (`d_out = d_in = d`) turns it into two equations, two unknowns, solvable by addition.

### `validate_exchange()`

Two comparisons, nothing else. `t4 < t1` means the client's own clock reports finishing before it started -- physically the client's clock, not the network, but still enough to poison the math. `t3 < t2` is the same idea on the server's side. Neither check inspects `t1` vs `t2` or `t3` vs `t4`, because a clock offset between client and server can legitimately put `t2` before `t1` or `t4` before `t3` -- that is exactly the thing `offset()` is trying to measure, so it cannot also be treated as an error.

### `offset()`

`((t2 - t1) + (t3 - t4)) / 2`. Read the docstring derivation to see the addition step (`(t2-t1) + (t4-t3) = 2*theta` under symmetry) reshuffled algebraically into this exact expression.

### `delay()`

`(t4 - t1) - (t3 - t2)`. Total time elapsed by the client's clock, minus time the server spent thinking. Note that `delay()` never needs the symmetry assumption at all -- it falls out of the same two equations regardless of whether `d_out` equals `d_in`.

## Failure Questions

Use the source file to answer these:

1. In the docstring's derivation, which term cancels out when you add `t2 - t1` and `t4 - t3` together, and what assumption is required for it to cancel exactly (not approximately)?
2. `validate_exchange()` does not compare `t2` against `t1`. Give a valid (non-malformed) exchange where `t2 < t1`, and explain why that is not a bug.
3. If the server's clock were exactly synchronized with the client's (`theta = 0`), what would `offset()` return for any well-formed exchange, and why does that follow from the formula without needing a special case in the code?
4. `delay()` does not appear anywhere in the formula for `offset()`. Why does the module still bother computing it?
5. Session 03 (`asymmetry.py`) says the symmetry assumption "cannot be detected" from the exchange itself. Looking only at `offset.py`, what information would you need that these four timestamps do not provide in order to check whether `d_out == d_in`?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/ntp/session_01_walkthrough.py
```

The walkthrough hand-computes `Exchange(1000, 1005, 1006, 1012)` -- offset `((1005-1000)+(1006-1012))/2 = -0.5`, delay `(1012-1000)-(1006-1005) = 11` -- then checks a symmetric zero-offset exchange, two independently malformed exchanges (`t4 < t1`, then `t3 < t2`), and one more exchange whose offset the reader should hand-verify before trusting the printed value.

## Done When

The learner can say all of the following without looking at notes:

- "Four timestamps, two unknowns worth solving for -- offset and delay -- and symmetry is what makes the system solvable."
- "`validate_exchange()` only rejects timestamps that violate one clock's own internal ordering, never a comparison across clocks."
- "`offset()` and `delay()` are pure arithmetic on the same two equations, read two different ways."

## References

- RFC 5905 Section 8 (On-Wire Protocol / clock offset and round-trip delay calculations)
