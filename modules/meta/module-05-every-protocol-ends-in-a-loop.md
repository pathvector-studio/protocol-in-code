# Session 05 / Module 05: Every Protocol Ends in a Loop

## Position

- Track: Same Shape
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/meta/module-05/index.html`
- Source file: `src/protocol_in_code/meta/the_loop.py`
- Walkthrough script: `examples/meta/session_05_walkthrough.py`

## Core Question

Twenty-two tracks, twenty-two protocols, twenty-two capstone files, each with its own event source — a BGP UPDATE, a DNS `resolve()` call, a clock tick, bytes off a pcap file — so what is actually left in common once every protocol-specific detail is stripped away, and can two of the most different capstones be shown, not just claimed, to share it?

## Outcome

By the end of this session, the learner should be able to:

- recite the six-step skeleton every capstone in this course was built on
- name the object and event source for at least five tracks without looking them up
- explain what `run_two_loops_side_by_side()` actually proves, and what it does not prove
- state the course's closing thesis in one sentence, in their own words, without naming a single protocol

## Read Order

1. Read the module docstring at the top of `the_loop.py` in full — it is this session's thesis statement
2. Read `LoopSummary`
3. Read `survey()` top to bottom, all 22 rows, without skimming
4. Read `common_skeleton()`
5. Read `run_two_loops_side_by_side()` and its docstring
6. Run `examples/meta/session_05_walkthrough.py`

## Read It Like Code

```python
LoopSummary(
    track,
    loop_object,
    event_source,
    decision_trace,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `track` | The course track's own short name — `bgp`, `dns`, `tcp`, and so on, 22 in total. |
| `loop_object` | The real class or module in that track's own capstone file that holds the loop's state — `bgp/speaker.py:ToySpeaker`, `tcp/speaker.py:ToyTcpEndpoint`, and so on. |
| `event_source` | What that track's loop actually receives as its one event per iteration — a message type, a clock tick, bytes off disk. This is the field that varies the most across all 22 rows. |
| `decision_trace` | `True` for every single row, on purpose — every capstone in this course appends a trace line to a decision it made. This uniformity, not any individual row, is the field worth reading twice. |

## Decision Flow

```text
common_skeleton(), the six steps every one of the 22 capstones was built on:
  1. hold state
  2. receive one event
  3. branch on state x event
  4. mutate + emit
  5. append one trace line
  6. repeat

run_two_loops_side_by_side(), one concrete proof of the same skeleton on two different event sources:
  dns: ToyResolver.resolve(DNSQuestion) walking a Zone tree -> one trace line: an answer found by delegation
  tcp: run_three_way_handshake(client, server)               -> one trace line: the server reaching Established
  different objects, different event sources, same skeleton -> both leave behind a trace line recording the decision
```

## Reading Lens

The important move in this session is to stop reading `survey()` as a list of 22 trivia facts and start asking, for every row:

- what plays the role of "state" for this track, and what plays the role of "one event"?
- could I describe this track's `event_source` without using any protocol-specific noun — is it fundamentally "a message arrives," "the clock ticks," or "bytes arrive from a file"?
- if I swapped this row's `loop_object` for a completely different track's, would `common_skeleton()`'s six steps still describe what happens next?

By this point in the course you have written, or at least read closely, code that does each of these six steps by hand, 22 times over, in 22 different files. This session is not teaching you a new shape — it is showing you the one shape you have already built, over and over, and naming it once, out loud.

## Toy Model Boundary

`survey()` is a literal, hand-written list, not introspection over the codebase — its own docstring says so plainly: "one row per capstone file, listed by hand so the count is honest, not introspected." Nothing in this file walks the `src/` tree counting classes or verifying that every track really does follow `common_skeleton()`; the six-step skeleton is this course's own retrospective claim about its own code, offered for the learner to check by hand against any of the 22 capstone files, not a property enforced or verified by a test.

`run_two_loops_side_by_side()` runs exactly two of the twenty-two loops — DNS and TCP — and pulls exactly one trace line from each. That is real code executing, not a metaphor, but it demonstrates the skeleton on two tracks, not all twenty-two; the other twenty rows in `survey()` are asserted by inspection, not run here. Note also that `quic` has no row of its own in `survey()` — the module docstring's "22 tracks, 22 capstone files" already accounts for this: QUIC's capstone shares HTTP's loop rather than building a separate one, which is itself a small instance of this session's own thesis — even "one loop per track" was not perfectly rigid across the course.

## Code Landmarks

### The module docstring

The entire course's closing argument, stated in one paragraph before any code runs: "BGP speaks UPDATE/WITHDRAW messages, NTP speaks the clock, a pcap parser speaks bytes off disk — the event source changes every time, but the shape wrapped around it never does." The final sentence is the thesis this whole track has been building toward: "the course taught 22 protocols, and it also taught one program, twenty-two times."

### `survey()`'s comment

"One row per capstone file, listed by hand so the count is honest, not introspected." This is the file being explicit about its own toy model boundary in a single line — worth reading as a model for how to disclose a limitation without apologizing for it.

### The `quic` gap in `survey()`

Count the rows: 22, and `quic` is not among them, yet the docstring claims "22 tracks." `http`'s row (`http/server_loop.py:ToyHttpServer`) is the one QUIC's own capstone shares — a detail only visible by noticing an absence, the same reading skill Session 03 (tristate) and Session 01 (ARP's degrade-not-delete) both asked for.

### `run_two_loops_side_by_side()`'s docstring

"Different event sources, same skeleton: both hold state, both branch on what just arrived, and both leave behind a trace line recording the decision they made." This function is the one place in the entire "Same Shape" track where the claim is not just described — it is executed, and the two resulting trace strings are real return values from real code, not illustrative prose.

## Failure Questions

Use the source file to answer these:

1. `survey()` returns exactly 22 rows. Which real track's capstone is *not* among them despite being a track taught earlier in the course, and what does the module docstring say accounts for its absence?
2. Every row in `survey()` has `decision_trace=True`. Is this field ever computed by inspecting the named `loop_object`'s source file, or is it a literal value written into every `LoopSummary(...)` call? What does your answer imply about what `decision_trace=True` is actually asserting?
3. `run_two_loops_side_by_side()` calls `resolver.resolve(...)` for DNS and `run_three_way_handshake(...)` for TCP. Which of `common_skeleton()`'s six steps does each of those two calls correspond to — is it "receive one event," or something broader?
4. The DNS trace line returned by `run_two_loops_side_by_side()` ends with `"(answer)"` and the TCP trace line ends with `"-> Established"`. Both are described in the docstring as "a trace line recording the decision they made" — what decision did each one record, using only the zone data and handshake call in this file?
5. `common_skeleton()` lists six steps, but `survey()`'s `LoopSummary` dataclass has only four fields, and none of them is named after any of the six steps. Which of the four `LoopSummary` fields, if any, corresponds to which of the six `common_skeleton()` steps — and which of the six steps has no corresponding field at all?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/meta/session_05_walkthrough.py
```

The walkthrough calls `survey()` and checks it returns exactly 22 rows with `decision_trace` true on every single one, confirms `common_skeleton()` has exactly 6 steps, runs `run_two_loops_side_by_side()` and checks both returned trace lines are non-empty and different from each other, and closes by printing the course's own thesis sentence.

## Done When

This is the course's closing session. "Done" here means the learner can do something no single earlier module asked for: name the shapes without the protocols.

The learner can say all of the following without looking at notes, and without naming a single specific protocol while saying them:

- "Every capstone in this course holds some state, receives one event, branches on state crossed with event, mutates the state and emits a reply or not, appends one trace line, and repeats."
- "The event source is the only thing that really varies between tracks — a message type, a clock tick, bytes off disk — the loop wrapped around it is the same loop every time."
- "This course taught 22 protocols. It also taught one program, twenty-two times."

If the learner can only produce these three sentences by first naming BGP, or DNS, or TCP, and reasoning outward from the specific protocol to the shape, this session is not yet done — the exit criterion is being able to state the shape first, and reach for a protocol only as an example if asked for one.

## References

- `modules/meta/module-01-the-expiring-dict-five-times.md` — the first shape this track made explicit
- `modules/meta/module-02-election-is-a-comparison-function-five-times.md` — the second shape
- `modules/meta/module-03-three-states-beat-two.md` — the third shape
- `modules/meta/module-04-silence-means-failure-everywhere.md` — the fourth shape
- `modules/dns/module-08-build-the-toy-resolver-loop.md` — one of the two loops actually run in this session
- `modules/tcp/module-11-build-the-toy-tcp-loop.md` — the other loop actually run in this session, and the capstone framing exemplar this whole track follows
