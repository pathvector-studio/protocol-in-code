# Session 02 / Module 02: Headers Come with Rules

## Position

- Track: HTTP/QUIC
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/http-quic/module-02/index.html`
- Source file: `src/protocol_in_code/http/headers.py`
- Walkthrough script: `examples/http-quic/session_02_walkthrough.py`

## Core Question

Once a request is parsed into a flat list of name/value pairs, what turns that list into "valid" or "invalid," and who decides?

## Outcome

By the end of this session, the learner should be able to:

- read the `RULES` table and say, for any header name in it, what a violation looks like
- explain why header names are folded before they are grouped
- explain why a missing `Host` on HTTP/1.1 is represented as an empty list of values rather than a special case
- explain why an unrecognized header never produces an issue

## Read Order

1. Read `HeaderProblem` and `HeaderIssue`
2. Read `normalize_name()`
3. Read `RULES` and each `_check_*` function it points to
4. Read `check_headers()`
5. Run `examples/http-quic/session_02_walkthrough.py`

## Read It Like Code

```python
HeaderIssue(
    name,
    problem,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `RULES` keys | Lowercase, folded header names. This is the complete set of headers this toy has an opinion about — everything else is silently allowed. |
| `RULES` values | Each is a `Callable[[tuple[str, ...]], HeaderIssue \| None]` — a function that receives *every* value seen for that name, not just the first. |
| `HeaderIssue.name` | The display name written into the issue (e.g. `"Host"`), independent of how the header was actually cased in the request. |
| `HeaderIssue.problem` | One `HeaderProblem` enum member — the reason, not the value that caused it. |

## Decision Flow

```text
group request.headers by normalize_name(name)          -> by_name: dict[str, list[str]]
version == HTTP/1.1 and "host" not in by_name            -> synthesize by_name["host"] = []
for each (name, values) in by_name:
    name not in RULES                                    -> skip (no opinion)
    RULES[name](values) returns an issue                  -> append to issues
    RULES[name](values) returns None                      -> no issue
return issues as a tuple, in dict-iteration order
```

## Reading Lens

The important move in this session is to stop thinking of "headers" as one flat list to scan and start asking:

- what is this header's name *after* folding, and which values does the rule function see, together, at once?
- is this a header `RULES` has an opinion about, or does it pass by default?
- for `Host` specifically: did the request even have one, or was its absence synthesized into the same code path that catches duplicates?

## Toy Model Boundary

Real header semantics are governed by RFC 9110's field-name registry, with hundreds of defined fields, list-based value syntax, and per-field combination rules (some fields may legally repeat, most core ones may not). `RULES` here is a three-entry table — `content-length`, `host`, `connection` — chosen to show three different validation shapes (a value-format check, a cardinality check, and an allowed-values check), not to be exhaustive. There is also no header-value size limit, no rejection of control characters in values, and no handling of `Content-Length` versus `Transfer-Encoding` conflicts.

## Code Landmarks

### `normalize_name()`

```python
def normalize_name(name: str) -> str:
    return name.strip().lower()
```

Strips surrounding whitespace and lowercases. This runs once, in `check_headers()`, before grouping — it is exported at the package level as `normalize_header_name`, since case folding is a concept the whole HTTP track reuses, not something private to this module.

### `RULES`

```python
RULES: dict[str, Callable[[tuple[str, ...]], HeaderIssue | None]] = {
    "content-length": _check_content_length,
    "host": _check_host,
    "connection": _check_connection,
}
```

The table itself *is* the lesson: to know what this toy validates, read the keys. To know how, read the three small functions. Each function receives a `tuple[str, ...]` — all values under that folded name — because headers may legally repeat, and a rule like "at most one Host" can only be enforced by seeing the whole group at once.

### `_check_host()`

```python
def _check_host(values: tuple[str, ...]) -> HeaderIssue | None:
    if len(values) == 0:
        return HeaderIssue("Host", HeaderProblem.MISSING_HOST)
    if len(values) > 1:
        return HeaderIssue("Host", HeaderProblem.DUPLICATE_HOST)
    return None
```

One function, two failure modes, driven entirely by `len(values)`. This only fires at all because of what happens just before `check_headers()` calls it.

### `check_headers()` — the Host synthesis

```python
if request.version == "HTTP/1.1" and "host" not in by_name:
    by_name["host"] = []
```

If `Host` is absent from the request entirely, this line manufactures an empty list under the `"host"` key *before* the rule loop runs. That empty list then flows into `_check_host()` exactly like a real empty group would, and `len(values) == 0` reports `MISSING_HOST`. One function ends up handling both "never sent" and "sent, but with nothing"-shaped inputs, because both look identical by the time `_check_host()` sees them. This synthesis is version-gated: on `HTTP/1.0`, a missing `Host` is never even checked.

### `check_headers()` — unknown headers

```python
rule = RULES.get(name)
if rule is None:
    continue
```

`RULES.get()`, not `RULES[name]` — a header with no entry in the table is skipped, not treated as an error. Silence is the default; only headers this toy explicitly knows about can ever produce an issue.

## Failure Questions

Use the source file to answer these:

1. A request has two headers: `("HOST", "a.com")` and `("host", "b.com")`. Does `check_headers()` report one issue or two? Which line makes them collapse into the same group?
2. A request has `Content-Length: 12` and `Content-Length: -1`. Which value(s) does `_check_content_length()` see, and does the order of iteration matter to the result?
3. An `HTTP/1.0` request has no `Host` header at all. What does `check_headers()` return for it, and which line explains why `_check_host()` is never even called?
4. A request has a header named `Cookie` with a garbage value. What does `check_headers()` return for it, and why?
5. What is the return type of a `_check_*` function when a header is entirely fine, and how does `check_headers()` distinguish "no issue" from "an issue that happens to be falsy"?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/http-quic/session_02_walkthrough.py
```

The walkthrough runs a clean request, a missing-Host request, a duplicate-Host request, a bad `Content-Length`, an unknown header that passes silently, and two spellings of `Host` (`HOST` vs `host`) folding into the same duplicate-detection path.

## Done When

The learner can say all of the following without looking at notes:

- "`RULES` is a lookup table from folded header name to a validator function — reading the table tells you exactly what this toy checks."
- "A validator sees every value for its header at once, as a tuple, which is the only way a cardinality rule like duplicate-Host can work."
- "A missing Host on HTTP/1.1 is turned into an empty values list before validation, so one function — not two — handles both missing and duplicate."

## References

- RFC 9110 (HTTP Semantics) — field names and the Host field
