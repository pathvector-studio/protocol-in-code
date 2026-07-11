# Session 01 / Module 01: A Segment Carries the Conversation State

## Position

- Track: TCP
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/tcp/module-01/index.html`
- Source file: `src/protocol_in_code/tcp/segment.py`
- Walkthrough script: `examples/tcp/session_01_walkthrough.py`

## Core Question

What does a TCP segment actually carry, and what makes a combination of flags and payload nonsensical before anyone even looks at what state the connection is in?

## Outcome

By the end of this session, the learner should be able to:

- name the five fields that make up a `Segment`
- explain why `flags` is a `frozenset[str]` instead of five booleans or a bitmask
- list every way `validate_segment()` can reject a segment, and in what order the checks run
- explain why "RST carrying a payload" is treated as invalid rather than merely unusual

## Read Order

1. Read `Segment`
2. Read `is_syn` / `is_ack` / `is_fin` / `is_rst`
3. Read `flags_label()`
4. Read `SegmentValidity`
5. Read `validate_segment()`
6. Run `examples/tcp/session_01_walkthrough.py`

## Read It Like Code

```python
Segment(
    seq,
    ack,
    flags,
    payload_len,
    window,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `seq` | The sequence number of the first byte of payload this segment carries (or the control-flag position if there is no payload). |
| `ack` | What the sender has received so far, valid only when the ACK flag is set. |
| `flags` | A `frozenset[str]` of control bits, e.g. `{"SYN", "ACK"}`. A set, not five separate booleans, because "which flags are present" is one fact, not five. |
| `payload_len` | How many bytes of data ride along. Zero for pure control segments. |
| `window` | The sender's advertised receive window at the moment this segment was sent. |

## Decision Flow

```text
flags not subset of FLAG_NAMES        -> BadFlagName
SYN and FIN both present              -> SynFinTogether
payload_len < 0                       -> NegativeLength
payload_len > 0 and RST present       -> PayloadWithoutSeqMeaning
otherwise                             -> Valid
```

## Reading Lens

The important move in this session is to stop thinking of a segment as "a packet with some flags on it" and start asking:

- which flags are present, and does that combination mean anything?
- does the payload agree with what the flags say this segment is for?
- is this check about the segment alone, or does it need the connection's state too?

Notice that `validate_segment()` never looks at a `ConnectionState`. Everything it checks is a fact about the segment by itself — state-dependent legality is Session 02's problem, not this one's.

## Toy Model Boundary

Real TCP segments carry a checksum, a data offset, options (MSS, window scaling, SACK, timestamps), and urgent-pointer plumbing tied to the URG flag. This toy keeps only the five fields that the rest of the course actually reasons about: `seq`, `ack`, `flags`, `payload_len`, `window`. `FLAG_NAMES` is deliberately just `{SYN, ACK, FIN, RST}` — no URG, no PSH, no ECE/CWR — because those four are what drive every state transition in Session 02.

`payload_len` is an integer count, not real bytes. The toy never constructs an actual payload buffer, because the reading target here is what the length means, not how to move bytes.

## Code Landmarks

### `Segment`

A frozen dataclass. Once built, a segment cannot be mutated — which matters because Session 02 passes segments around and builds replies from their fields without ever needing to worry that a segment changed underneath it.

### `is_syn` / `is_ack` / `is_fin` / `is_rst`

Four one-line predicates, each just a membership test on `flags`. Small enough to not need comments, and every other module in this track calls them instead of touching `segment.flags` directly.

### `flags_label()`

Renders flags in "the conventional wire order" (`SYN, ACK, FIN, RST`), not set-iteration order. A `frozenset` has no order of its own — this function is where the human-readable rendering imposes one.

### `validate_segment()`

The main reading target. Four early-return checks, evaluated in a fixed sequence. Notice the check order: an unknown flag is rejected before the SYN+FIN check even runs, and negative length is rejected before the RST-payload check.

## Failure Questions

Use the source file to answer these:

1. A segment has `flags=frozenset({"SYN", "FIN", "URG"})`. Which `SegmentValidity` comes back, and why does that check win over the SYN+FIN check?
2. Why is `payload_len < 0` treated as a distinct validity outcome from `payload_len > 0` on an RST, instead of being folded into the same check?
3. Is a segment with `flags=frozenset()` and `payload_len=0` valid? Trace `validate_segment()` to confirm.
4. Does `validate_segment()` reject a segment with `ack` set but no ACK flag present? Read the function body to be sure, not the docstring.
5. Why does an RST with `payload_len=0` pass validation, but the same RST with `payload_len=1` fail?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tcp/session_01_walkthrough.py
```

The walkthrough builds one valid control segment, one valid data segment, and one segment for each of the four ways `validate_segment()` can reject input, then checks `flags_label()` renders in wire order.

## Done When

The learner can say all of the following without looking at notes:

- "A segment is five fields — flags is a set of names, not a bitmask I have to decode."
- "Validity is checked before state; SYN+FIN together is always wrong, no matter what state the connection is in."
- "An RST carrying a payload is rejected because a reset has no sequence meaning for data it claims to carry."

## References

- RFC 9293 Section 3.1 (Header Format)
- RFC 9293 Section 3.4 (Sequence Numbers — payload/control-flag sequence semantics)
- RFC 9293 Section 3.8.6 (Managing the Window — the `window` field this segment carries)
