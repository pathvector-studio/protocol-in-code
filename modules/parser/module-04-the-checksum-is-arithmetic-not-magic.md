# Session 04 / Module 04: The Checksum Is Arithmetic, Not Magic

## Position

- Track: Packet Parser
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/parser/module-04/index.html`
- Source file: `src/protocol_in_code/parser/checksum.py`
- Walkthrough script: `examples/parser/session_04_walkthrough.py`

## Core Question

The IPv4 checksum is not a hash, not a CRC, and not a library call — it is 16-bit addition with the overflow folded back in. What exactly does that addition do, and why does a valid header sum to all-ones instead of zero?

## Outcome

By the end of this session, the learner should be able to:

- compute `ones_complement_sum()` on a short byte string by hand
- explain what happens to an odd trailing byte before it is summed
- explain end-around carry: why a carry out of bit 16 is added back into bit 0 instead of being discarded
- state the exact condition `verify_checksum()` checks, and why it includes the checksum field itself in the sum

## Read Order

1. Read the module comment at the top of the file
2. Read `ones_complement_sum()`
3. Read `internet_checksum()`
4. Read `verify_checksum()`
5. Run `examples/parser/session_04_walkthrough.py`

## Read It Like Code

```python
ones_complement_sum(data: bytes) -> int
internet_checksum(data: bytes) -> int
verify_checksum(header: bytes) -> bool
```

There is no dataclass in this file. That is deliberate — see Reading Lens.

## Fields That Matter

This module has no records to hold state; it is three functions and two constants. The constants are the fields that matter:

| Name | Why it matters |
|---|---|
| `WORD_MASK` (`0xFFFF`) | Isolates the low 16 bits after each addition — the "fold the carry back in" mask. |
| `VALID_SUM` (`0xFFFF`) | The target a correctly-checksummed header must sum to, checksum field included. |

## Decision Flow

```text
ones_complement_sum(data):
  odd length            -> pad with one zero byte before summing
  for each 16-bit word:
      total += word
      total = (total & 0xFFFF) + (total >> 16)   -> end-around carry, every iteration

internet_checksum(data)  = ~ones_complement_sum(data) & 0xFFFF
verify_checksum(header)  = ones_complement_sum(header) == 0xFFFF
```

## Reading Lens

The important move in this session is to stop looking for a formula and start tracing the loop by hand, one word at a time:

- what is `total` immediately after each addition, before the carry fold?
- does this addition overflow 16 bits, and if so, where does the overflow go?
- when `verify_checksum()` sums a header, is the checksum field itself part of that sum, or excluded?

This file has no dataclasses, on purpose, the same way `tcp/seqnum.py` has none — the lesson is that some protocol mechanics are pure integer arithmetic, with no state worth naming in a type. Wrapping `total` in a class here would hide the one thing worth seeing: three lines inside a loop are the entire algorithm.

## Toy Model Boundary

This module computes a checksum from a full byte string every time. Real implementations often maintain the sum incrementally — updating it in place when a single field changes, rather than resumming the whole header — which this file does not attempt. There is also no TCP/UDP pseudo-header here: RFC 1071's algorithm applies to any byte string, but computing a TCP or UDP checksum requires summing a pseudo-header (source and destination IP, protocol, length) ahead of the real one, and that construction is out of scope for this module. `ones_complement_sum()` is the general-purpose primitive; what gets fed into it is a later session's problem.

## Code Landmarks

### The module comment

States the whole lesson in three lines: ones-complement sum of 16-bit words, complemented at the end, per RFC 1071 section 4.1. Everything below is that sentence made literal.

### `ones_complement_sum()`'s padding line

`data if len(data) % 2 == 0 else data + b"\x00"` — an odd-length input gets exactly one zero byte appended before the loop ever runs. The pad is not part of the returned sum's length accounting; it only exists to make the last word whole.

### `ones_complement_sum()`'s carry line

`total = (total & WORD_MASK) + (total >> 16)` runs after every single word, not just at the end. This is what "end-around carry" means in code: whatever spilled past bit 15 is added back at bit 0 immediately, so the next addition starts from a folded value.

### `internet_checksum()`

One line: bitwise NOT of the sum, masked back to 16 bits. This is the value a sender writes into the checksum field before transmission.

### `verify_checksum()`

Does not call `internet_checksum()`. It sums the header as received — checksum field included — and asks whether that sum equals `0xFFFF`. This is the receiver-side check, and it is a different call shape from the sender-side one on purpose.

## Failure Questions

Use the source file to answer these:

1. `ones_complement_sum()` runs `total = (total & WORD_MASK) + (total >> 16)` after adding every word, not once at the end. Would summing all the words first and folding the carry only once at the very end give the same answer? Why does the loop fold it every time instead?
2. A header's checksum field is set to `internet_checksum(header_without_checksum)`. When `verify_checksum()` later sums the complete header — checksum field included — why does that sum come out to `0xFFFF` instead of `0x0000`?
3. `ones_complement_sum(bytes([0xFF]))` pads to `0xFF00` before summing, not `0x00FF`. What would change about the result if the pad byte were prepended instead of appended?
4. `internet_checksum()` is `~ones_complement_sum(data) & WORD_MASK`. Without the `& WORD_MASK`, what would Python's `~` operator return, and why would that break the function?
5. If a single bit anywhere in a header (including the checksum field itself) is flipped in transit, does `verify_checksum()` reliably return `False`? Is there any single-bit flip the sum-based check in this file cannot detect?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/parser/session_04_walkthrough.py
```

The walkthrough sums three words by hand, pads an odd-length input, demonstrates end-around carry on a value chosen to overflow, builds a real 20-byte IPv4 header and checksums it with `internet_checksum()`, confirms `verify_checksum()` on the resulting header sums to `0xFFFF`, and shows a single flipped byte failing verification.

## Done When

The learner can say all of the following without looking at notes:

- "The checksum is 16-bit addition with the overflow folded back into bit 0 after every word — end-around carry, not a special algorithm."
- "A valid header including its own checksum field sums to all-ones, `0xFFFF`, not zero — because the checksum was built as the complement of the rest."
- "There is no dataclass in this file because the entire lesson is that some protocol mechanics are pure arithmetic, with nothing worth naming as state."

## References

- RFC 1071 Section 4.1 (the ones-complement sum algorithm)
