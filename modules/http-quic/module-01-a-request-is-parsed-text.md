# Session 01 / Module 01: A Request Is Parsed Text

## Position

- Track: HTTP/QUIC
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/http-quic/module-01/index.html`
- Source file: `src/protocol_in_code/http/parse.py`
- Walkthrough script: `examples/http-quic/session_01_walkthrough.py`

## Core Question

Before any header semantics or routing, what shape does raw HTTP text have to match, and what breaks that shape?

## Outcome

By the end of this session, the learner should be able to:

- name the four `ParseOutcome` values and which check produces each one
- explain why the request line is checked before any header line
- explain why a trailing `\r\n\r\n` produces two empty strings, not one, after splitting
- state which HTTP versions this toy accepts and why the rest are rejected outright

## Read Order

1. Read `SUPPORTED_VERSIONS` and `ParseOutcome`
2. Read `Request` and `ParseResult`
3. Read `_parse_request_line()`
4. Read `_parse_header_line()`
5. Read `parse_request()`
6. Run `examples/http-quic/session_01_walkthrough.py`

## Read It Like Code

```python
Request(
    method,
    target,
    version,
    headers,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `method` | The first token of the request line. Not validated against a known verb list here — any non-empty token passes. |
| `target` | The second token. Path, query string, or `*` — this layer does not interpret it. |
| `version` | The third token. Gates everything after it: an unsupported version stops parsing before headers are even read. |
| `headers` | A tuple of `(name, value)` pairs, in arrival order, duplicates and all. Nothing is deduplicated or folded at this layer. |

## Decision Flow

```text
lines has 0 lines after stripping trailing blanks -> BadRequestLine
request line does not split into exactly 3 tokens -> BadRequestLine
any of method/target/version is empty             -> BadRequestLine
version not in SUPPORTED_VERSIONS                  -> UnsupportedVersion
any remaining line has no ":"                      -> BadHeaderLine
otherwise                                          -> Ok
```

## Reading Lens

The important move in this session is to stop thinking of an HTTP request as "a URL with some headers" and start asking:

- what are the exact three tokens on the request line, and did the split produce exactly three?
- how many trailing empty strings does `raw.split("\r\n")` leave behind, and why does a single `if` undercount them?
- which outcome does the function return the moment it finds a problem, and what does it skip checking after that?

## Toy Model Boundary

Real HTTP/1.1 parsing handles obs-fold (header values continued on the next line with leading whitespace), chunked and content-length bodies, and a request line grammar defined by ABNF rather than a plain `split(" ")`. This lesson keeps parsing to request-line-plus-headers only — there is no body handling anywhere in `parse.py`. `_parse_request_line()` also does not reject method or target strings containing spaces beyond the split, and does not validate `target` as a well-formed request-target; the reading target is the three-outcome branching, not full RFC 9112 conformance.

## Code Landmarks

### `SUPPORTED_VERSIONS`

A two-element tuple, `("HTTP/1.0", "HTTP/1.1")`. `HTTP/2.0` and `HTTP/0.9` are both rejected the same way, by the same membership test — the version string is compared literally, not parsed into major/minor numbers.

### `parse_request()` trailing-blank stripping

```python
while lines and lines[-1] == "":
    lines = lines[:-1]
```

This is a `while`, not an `if`. A request ending in `\r\n\r\n` splits into a trailing empty string for the blank header/body separator line, *and* another trailing empty string from the final `\r\n` itself — two empties, not one. A single `if` here was a real bug caught in verification: it left one stray empty string in `lines`, which `_parse_header_line()` then rejected as `BadHeaderLine` because an empty string contains no `:`.

### `_parse_request_line()`

Returns `None` — not an outcome — on any structural failure. `parse_request()` is the only place that turns `None` into `ParseOutcome.BAD_REQUEST_LINE`. Note the emptiness check runs after the length check: three empty-string tokens (e.g. from `"  "`) would still fail on `not method`.

### `_parse_header_line()`

`":" not in line` is checked before `partition`. `partition` always succeeds (it returns `(line, "", "")` if there's no separator), so the explicit membership check is what actually catches the missing-colon case — the `_, _, _` shape of `partition`'s result alone would not.

### `parse_request()` main loop

Header parsing happens in `lines[1:]` — the request line itself, `lines[0]`, is never re-examined as a header. The loop returns `ParseOutcome.BAD_HEADER_LINE` on the *first* bad line, so a request with a good header, then a bad one, then another good one still reports only `BadHeaderLine` and constructs no `Request`.

## Failure Questions

Use the source file to answer these:

1. Why does `"GET /index.html\r\nHost: example.com\r\n\r\n"` come back `BAD_REQUEST_LINE` rather than `BAD_HEADER_LINE`, even though it has a well-formed header line?
2. A raw string ends in exactly one `\r\n\r\n`. How many empty strings does `raw.split("\r\n")` leave at the end of `lines`, and which line of code removes all of them?
3. Why is `version not in SUPPORTED_VERSIONS` checked before the header loop runs at all, instead of after headers are parsed?
4. If `raw` is `"GET / HTTP/1.1\r\nHost: example.com\r\nBad Line\r\nX: y\r\n\r\n"`, does parsing report anything about the `X: y` line? Why or why not?
5. What does `parse_request("")` return, and which line in `parse_request()` produces that result?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/http-quic/session_01_walkthrough.py
```

The walkthrough shows a good request parsing cleanly, three distinct kinds of malformed input each producing their own `ParseOutcome`, and confirms that trailing blank lines beyond the normal separator do not break parsing.

## Done When

The learner can say all of the following without looking at notes:

- "The request line is checked, then the version, then headers — in that order, and each stage can stop parsing before the next begins."
- "Splitting on `\r\n` after a `\r\n\r\n` terminator leaves two trailing empty strings, not one, which is why the stripping loop must be a `while`."
- "An unsupported version is rejected before a single header line is looked at."

## References

- RFC 9112 (HTTP/1.1 Message Syntax and Routing)
