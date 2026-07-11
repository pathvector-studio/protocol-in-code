# Session 06 / Module 06: Chunked Is a Parser State Machine

## Position

- Track: HTTP/QUIC
- Session: 06
- Site lesson: `pathvector-site/courses/protocols-in-code/http-quic/module-06/index.html`
- Source file: `src/protocol_in_code/http/chunked.py`
- Walkthrough script: `examples/http-quic/session_06_walkthrough.py`

## Core Question

Chunked transfer encoding is a stream of alternating size-lines and data — what single field tracks where the parser is in that alternation, and what makes an error state permanent once entered?

## Outcome

By the end of this session, the learner should be able to:

- name the five states of `ChunkParserState` and what input each one expects next
- explain why `feed_line()` and `feed_data()` are two separate entry points rather than one
- trace `bytes_needed` from a size-line through to the data-length check
- explain why `DONE` and `ERROR` are sticky — once entered, no further input changes them except into `ERROR`

## Read Order

1. Read `ChunkParserState`
2. Read `ChunkParser`
3. Read `feed_line()`
4. Read `feed_data()`
5. Read `parse_chunked()`
6. Run `examples/http-quic/session_06_walkthrough.py`

## Read It Like Code

```python
ChunkParser(
    state,
    bytes_needed,
    chunks,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `state` | The entire story of where the parser is. Every method reads it first and nearly always sets it last. |
| `bytes_needed` | Set by `feed_line()` when a size-line is parsed; checked by `feed_data()` against the length of the data actually given. |
| `chunks` | Accumulates one string per successfully parsed chunk. Only meaningful once `state` reaches `DONE`. |

## Decision Flow

```text
state == SIZE_LINE,  line parses as hex, size > 0   -> DATA          (bytes_needed set)
state == SIZE_LINE,  line parses as hex, size == 0   -> DONE          (terminator chunk)
state == SIZE_LINE,  line does not parse as hex       -> ERROR
state == DATA,        len(data) == bytes_needed        -> DATA_CRLF
state == DATA,        len(data) != bytes_needed        -> ERROR
state == DATA_CRLF,   line == ""                        -> SIZE_LINE
state == DATA_CRLF,   line != ""                        -> ERROR
state in (DONE, ERROR)                                    -> ERROR   (any further feed)
```

## Reading Lens

The important move in this session is to stop reading `feed_line()` and `feed_data()` as two independent parsing functions and start asking, on every call:

- what state was the parser in before this call?
- which of the two entry points does that state expect next — a line or raw data?
- did this call leave `state` somewhere that accepts more input, or somewhere terminal?

## Toy Model Boundary

Real chunked coding (RFC 9112) allows chunk extensions after the size on the size-line (`size;ext=value`) and trailer fields after the terminating zero-size chunk, both of which this parser ignores entirely — a size-line here is just a bare hex number, full stop, and there is no trailer-field state at all. There is also no cap on `bytes_needed` and no protection against a maliciously huge declared chunk size; this toy trusts the size-line completely once it parses as hex.

## Code Landmarks

### `feed_line()` — the SIZE_LINE branch

`int(line.strip(), 16)` wrapped in a `try/except ValueError`. A size of exactly `0` is the terminator and jumps straight to `DONE`, skipping `DATA` and `DATA_CRLF` entirely for that chunk.

### `feed_line()` — the trailing `else`

Any state that is not `SIZE_LINE` and not `DATA_CRLF` falls into the final `else: parser.state = ChunkParserState.ERROR`. This is what makes calling `feed_line()` while in `DONA`, `DONE`, or `ERROR` always land on `ERROR` — there is no explicit `if state is DONE` check; it falls out of exhausting the other branches.

### `feed_data()`

Two separate ways to reach `ERROR`: being called while `state is not DATA` at all, or being called in `DATA` with a `data` string whose length does not equal `bytes_needed`. Both checks return early; only the exact-length case appends to `chunks` and advances to `DATA_CRLF`.

### `parse_chunked()`

The convenience wrapper's `while` condition is `parser.state not in (DONE, ERROR)` — it stops driving the parser the moment either terminal state is reached, including mid-list if `ERROR` happens early. It also treats running out of `lines` before reaching `DONE` as its own `ERROR` case, distinct from any state-machine error.

## Failure Questions

Use the source file to answer these:

1. `ChunkParser` starts in state `DONE`... no — trace it: what is the default `state` value in the dataclass, and which method would you have to call first for the parser to ever leave it?
2. Call `feed_line(parser, "0")` on a fresh parser, then call `feed_line(parser, "5")` on the same parser object. What state does it end in, and which branch of `feed_line()` — not the `SIZE_LINE` branch — produces that result?
3. `feed_data()` checks `len(data) != parser.bytes_needed`. If a size-line declares `5` but the data given is `"hell"` (4 characters), what state results, and does any part of `"hell"` end up in `chunks`?
4. `parse_chunked()`'s `while` loop checks `parser.state is ChunkParserState.DATA` to decide whether to call `feed_data()` instead of `feed_line()`. Is there any state other than `DATA` that would misroute a data line into `feed_line()` and produce a confusing error rather than a clean one?
5. Once `state` is `ERROR`, is there any sequence of calls to `feed_line()` or `feed_data()` that returns the parser to a non-`ERROR` state? Point to the exact line that guarantees your answer.

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/http-quic/session_06_walkthrough.py
```

The walkthrough drives one chunk through `SIZE_LINE -> DATA -> DATA_CRLF -> SIZE_LINE -> DONE` with the state asserted after each feed, assembles a two-chunk body through `parse_chunked()`, and then shows a bad hex size and a post-DONE feed both landing on the same sticky `ERROR` state.

## Done When

The learner can say all of the following without looking at notes:

- "The parser's entire behavior is a function of one field, `state`, plus whatever the current input is."
- "feed_line() and feed_data() are not interchangeable — calling the wrong one for the current state is itself an error path."
- "DONE and ERROR are both terminal, but only ERROR is what every misuse funnels into; feeding a finished parser more input does not silently succeed."

## References

- RFC 9112 Section 7.1 (Chunked Transfer Coding)
