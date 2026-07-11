# Session 05 / Module 05: A Cert Is for a Name, Not a Server

## Position

- Track: TLS
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/tls/module-05/index.html`
- Source file: `src/protocol_in_code/tls/hostname.py`
- Walkthrough script: `examples/tls/session_05_walkthrough.py`

## Core Question

A chain can be perfectly trusted and still be the wrong certificate for the connection you're making. What decides whether a certificate is allowed to speak for the hostname you asked for?

## Outcome

By the end of this session, the learner should be able to:

- explain why exact matches are checked before any wildcard match
- state precisely which label a wildcard is allowed to cover
- explain why `*.example.com` does not match `a.b.example.com`
- explain why `*.example.com` does not match `example.com` itself
- explain why `w*.example.com` is always rejected as a wildcard

## Read Order

1. Read `HostnameVerdict` and `HostnameMatch`
2. Read `matches_exact()`
3. Read `matches_wildcard()`
4. Read `match_hostname()`
5. Run `examples/tls/session_05_walkthrough.py`

## Read It Like Code

```python
HostnameMatch(
    verdict,
    matched_san,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `verdict` | One of `MATCHED_EXACT`, `MATCHED_WILDCARD`, `NO_MATCH`. Which branch fired, not just whether it matched. |
| `matched_san` | The specific SAN entry that won, or `None` on `NO_MATCH`. Lets you point at *which* name in the certificate was responsible. |

## Decision Flow

```text
any san: hostname == san (case-insensitive)          -> MatchedExact
any san: san is "*.<suffix>" and hostname is          -> MatchedWildcard
  exactly one non-empty, dot-free label + <suffix>
otherwise                                             -> NoMatch
```

## Reading Lens

The important move in this session is to stop thinking of wildcard matching as "does the string end with the right suffix" and start asking:

- what is left over after the suffix is stripped off — and does that leftover contain a dot?
- is the exact-match loop checked before or after the wildcard loop, and does that order ever change the outcome?
- is `san` required to literally start with `*.`, or would `w*.example.com` also qualify as a wildcard?

## Toy Model Boundary

Real certificate validation also falls back to the deprecated Common Name field when SAN is absent (this code never does — SANs are the only input `match_hostname()` accepts), and real clients apply public-suffix-list rules to stop wildcards like `*.co.uk` from being treated as safe. Neither exists here: `match_hostname()` is pure string comparison against whatever `san_names` tuple it's handed, with RFC 6125's leftmost-label rule as the only constraint on wildcards.

## Code Landmarks

### `matches_exact()`

```python
return hostname.lower() == san.lower()
```

Case-insensitivity is the entire rule. No suffix logic, no labels — just a lowered string comparison.

### `matches_wildcard()`

```python
if not san.startswith("*."):
    return False
```

The wildcard marker must be exactly `*.` at the start of the SAN. `w*.example.com` fails this check immediately — it never even reaches the label logic, so it's rejected regardless of what hostname you test it against.

```python
wildcard_suffix = san[1:]  # keeps the leading dot, e.g. ".example.com"
if not hostname.endswith(wildcard_suffix):
    return False

remaining = hostname[: -len(wildcard_suffix)]
return len(remaining) > 0 and "." not in remaining
```

`remaining` is whatever the wildcard would have to stand for. Two conditions gate it: it must be non-empty (so the wildcard can't match "nothing," which is what would let `*.example.com` match `example.com`), and it must contain no dot (so the wildcard can't silently swallow an extra label, which is what would let `*.example.com` match `a.b.example.com`).

### `match_hostname()`

```python
for san in san_names:
    if matches_exact(hostname, san):
        return HostnameMatch(HostnameVerdict.MATCHED_EXACT, san)

for san in san_names:
    if matches_wildcard(hostname, san):
        return HostnameMatch(HostnameVerdict.MATCHED_WILDCARD, san)
```

Two full passes over `san_names`. Every SAN is checked for an exact match before any SAN is checked for a wildcard match — so if a certificate happens to list both `www.example.com` and `*.example.com`, the exact entry wins even if it appears later in the tuple.

## Failure Questions

Use the source file to answer these:

1. If `san_names` contains `*.example.com` at index 0 and `www.example.com` at index 1, and the hostname is `www.example.com`, which verdict wins, and why does the two-loop structure of `match_hostname()` guarantee that regardless of tuple order?
2. Why does `matches_wildcard("a.b.example.com", "*.example.com")` return `False` — walk through what `remaining` evaluates to.
3. Why does `matches_wildcard("example.com", "*.example.com")` return `False` — what does `remaining` equal, and which of the two guard conditions rejects it?
4. `matches_wildcard()` checks `san.startswith("*.")` before computing `wildcard_suffix`. What would go wrong if `w*.example.com` were allowed to reach the `remaining` computation?
5. Does `match_hostname()` ever lowercase `san_names` before comparison, or is that done per-call inside each helper? What would break if a caller compared `san_names` directly without going through `matches_exact`/`matches_wildcard`?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tls/session_05_walkthrough.py
```

The walkthrough checks an exact match, a case-insensitive exact match, a valid wildcard match, a wildcard that fails because it would have to span two labels, a wildcard that fails against the bare domain, a partial-label wildcard that's rejected outright, and a hostname with no owning SAN at all.

## Done When

The learner can say all of the following without looking at notes:

- "Exact matches are checked in a full pass before any wildcard is checked, not interleaved."
- "A wildcard covers exactly one non-empty label and nothing more — not zero labels, not two."
- "`w*.example.com` is rejected before label logic even runs, because the SAN doesn't start with `*.`."
- "This is string matching against a SAN list — there's no CN fallback and no public-suffix awareness here."

## References

- RFC 6125 Section 6.4.3 (wildcard certificate matching rules)
