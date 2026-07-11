# Session 02 / Module 02: Agreement Is a Set Intersection

## Position

- Track: TLS
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/tls/module-02/index.html`
- Source file: `src/protocol_in_code/tls/negotiate.py`
- Walkthrough script: `examples/tls/session_02_walkthrough.py`

## Core Question

When a client and a server each bring an ordered list of what they support, whose order decides the final pick?

## Outcome

By the end of this session, the learner should be able to:

- explain negotiation as two steps: intersect, then order
- state which side's preference order wins the pick, and prove it from the loop that does the picking
- name the three `NegotiationOutcome` values and which functions can produce which
- explain why an empty ALPN offer is "no overlap," not a crash

## Read Order

1. Read `NegotiationOutcome`
2. Read `NegotiationResult`
3. Read `choose_version()`
4. Read `choose_suite()`
5. Read `choose_alpn()`
6. Run `examples/tls/session_02_walkthrough.py`

## Read It Like Code

```python
NegotiationResult(
    outcome,
    chosen,
    note,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `outcome` | One of `CHOSEN`, `NO_OVERLAP`, `NO_VERSION_OVERLAP` - the shape of what happened. |
| `chosen` | The winning value, or `None` if nothing was chosen. Only meaningful when `outcome is CHOSEN`. |
| `note` | A short, human-readable reason. Useful for logging, not for branching logic. |

## Decision Flow

```text
set(client) & set(server_preference) empty  -> NO_OVERLAP (or NO_VERSION_OVERLAP for versions)
otherwise: walk server_preference in order,
first candidate that is in the overlap set  -> CHOSEN, that candidate
```

## Reading Lens

The important move in this session is to stop thinking of negotiation as "whatever the client asked for first" and start asking:

- what is the overlap between the two sets, ignoring order?
- once the overlap set exists, whose list gets walked to break the tie?
- would the outcome change if the client's list were reordered? (it would not - only membership in the set matters for the client)

## Toy Model Boundary

Real TLS 1.3 negotiation can also produce a HelloRetryRequest when the server wants a different key share group than the client offered, and version negotiation interacts with a `supported_versions` extension rather than a flat list. This module has no retry path at all: every negotiation here is a single pass over already-declared lists, so it can only end in `CHOSEN` or one of the two overlap-failure outcomes.

There is also no compatibility fallback logic (no downgrade protection mechanism, no GREASE values) - the three functions are pure set intersection plus ordered pick, nothing more.

## Code Landmarks

### `choose_version()`

`set(client_versions) & set(server_preference)` computes the overlap first, discarding all order information from the client's list. The `for candidate in server_preference` loop that follows is what reintroduces order - and it iterates the *server's* list, not the client's.

### `choose_suite()`

Structurally identical to `choose_version()`, with `NO_OVERLAP` instead of `NO_VERSION_OVERLAP` as the empty-overlap outcome. Read the two functions side by side to see they are the same algorithm applied to a different field.

### `choose_alpn()`

Same algorithm again. Its docstring is the thesis for this function: ALPN is optional, so an empty offer on either side produces `NO_OVERLAP`, a normal `NegotiationResult` - not an exception, not a special case.

### The trailing `return` after each loop

Every function ends with a second `NO_OVERLAP`/`NO_VERSION_OVERLAP` return after the `for` loop, even though the loop is guaranteed to find a match once `overlap` is non-empty. Look closely at why that line can never actually execute - it is defensive, not reachable.

## Failure Questions

Use the source file to answer these:

1. `choose_version(("TLS1.3", "TLS1.2"), ("TLS1.2",))` - the client's first preference is TLS1.3, but the server only supports TLS1.2. What is `.chosen`, and which side's list determined that value?
2. Both `choose_suite()` and `choose_alpn()` return `NegotiationOutcome.NO_OVERLAP` on empty overlap. Given only this file, how would calling code tell a failed ALPN negotiation apart from a failed cipher suite negotiation?
3. If `client_versions` contains a version that also appears twice in `server_preference`, does that change which candidate is chosen? Why or why not, given what `set()` does to the server list before the loop runs?
4. Is it possible for `choose_alpn()` to return `NegotiationOutcome.CHOSEN` with `chosen is None`? Trace the function to justify your answer.
5. The final `return` statement in each function is, in practice, unreachable once `overlap` is non-empty. What guarantees that the `for` loop always finds a match in that case?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tls/session_02_walkthrough.py
```

The walkthrough deliberately reverses client and server preference order for version, cipher suite, and ALPN, and shows the server's order wins every time, then drives each function into its no-overlap outcome.

## Done When

The learner can say all of the following without looking at notes:

- "Negotiation is intersect first, then let the server's order break the tie - the client's order never matters once the overlap set exists."
- "`choose_version`, `choose_suite`, and `choose_alpn` are the same algorithm three times, differing only in which outcome they report on failure."
- "An empty ALPN overlap is not an error condition, it is a normal `NO_OVERLAP` result, because ALPN is optional."

## References

- RFC 8446 Section 4.1.3 (Server Hello)
- RFC 8446 Section 4.1.1 (Cryptographic Negotiation)
- RFC 7301 (Application-Layer Protocol Negotiation Extension)
