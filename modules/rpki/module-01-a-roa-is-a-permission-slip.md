# Session 01 / Module 01: A ROA Is A Permission Slip

## Position

- Track: RPKI
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/rpki/module-01/index.html`
- Source file: `src/protocol_in_code/rpki/roa.py`
- Walkthrough script: `examples/rpki/session_01_walkthrough.py`

## Core Question

What is a ROA, stripped of everything except the three facts it actually asserts?

## Outcome

By the end of this session, the learner should be able to:

- name the three fields of a ROA and what each one asserts
- explain why `max_length` cannot be less specific than the prefix itself
- explain what `MALFORMED_PREFIX` catches versus what `INVALID_MAX_LENGTH` catches
- explain why this toy is IPv4-only and what a real ROA adds on top

## Read Order

1. Read the module docstring
2. Read `Roa`
3. Read `RoaValidity`
4. Read `_parse_prefix()`
5. Read `validate_roa()`
6. Run `examples/rpki/session_01_walkthrough.py`

## Read It Like Code

```python
Roa(
    prefix,
    max_length,
    origin_asn,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `prefix` | The address range the holder is authorizing. Everything downstream starts by parsing this string. |
| `max_length` | How specific an announcement of `prefix` is allowed to be. This is a ceiling on specificity, not a second prefix. |
| `origin_asn` | The one AS number permitted to originate `prefix` (down to `max_length`). |

## Decision Flow

```text
prefix does not parse                          -> MALFORMED_PREFIX
max_length < prefix's own length                -> INVALID_MAX_LENGTH
max_length > IPV4_MAX_PREFIXLEN (32)             -> INVALID_MAX_LENGTH
otherwise                                        -> VALID
```

## Reading Lens

The important move in this session is to stop treating a ROA as a network object and start reading it as a data record with exactly one job: authorize one origin AS to announce one address range, no more specifically than one bound.

- what does `prefix` claim, as an address range?
- does `max_length` narrow that range, or does it try to widen it?
- is `origin_asn` the only thing this ROA has an opinion about?

This session sets up `rpki/covering.py` (session 02) and `rpki/validate.py` (session 03): both of those modules take a well-formed `Roa` as a given and ask harder questions about announcements against it. Nothing here talks to BGP at all — that connection is `bgp/validation.py`'s `VRP`, which is the RPKI-to-Router-Protocol shape of the same three facts. This session is the plainer, pre-VRP version: the permission slip on its own, before it is turned into router-usable data.

## Toy Model Boundary

A real ROA is a cryptographically signed object issued by a CA in the RPKI hierarchy (RFC 6482): it has a signer, a validity period, and a chain of trust back to a trust anchor, and it can authorize multiple prefixes — including IPv6 — in one object. This toy has none of that. `Roa` is just the payload: three fields, no signature, no issuer, no expiry, and IPv4 only. The lesson here is what the payload *means*; how it gets signed, published, and fetched is out of scope.

## Code Landmarks

### `Roa`

A frozen dataclass, three fields, nothing else. Frozen because a permission slip does not mutate — a new ROA replaces an old one, it does not edit it in place.

### `RoaValidity`

Three outcomes, not two. Notice this is not `bool` — a well-formed ROA is `VALID`, and there are two distinct ways to be malformed, not one generic "bad ROA" bucket.

### `_parse_prefix()`

The one place `ip_network()` gets called. It swallows `ValueError` and `AddressValueError` and returns `None` instead of raising — that `None` is what `validate_roa()` turns into `MALFORMED_PREFIX`. Note that `ip_network()` is strict by default: a string with host bits set (like `203.0.113.5/24` instead of `203.0.113.0/24`) is *also* a parse failure here, not a silent normalization.

### `validate_roa()`

The main reading target. Two guard checks in sequence, `VALID` only if both pass. Read the comparison closely: `roa.max_length < network.prefixlen` is what rejects an attempt to authorize a range *broader* than the prefix itself.

## Failure Questions

Use the source file to answer these:

1. A ROA has `prefix="203.0.113.0/24"` and `max_length=20`. What verdict does it get, and which line decides?
2. Why does `203.0.113.5/24` (host bits set) fail to parse instead of being silently corrected to `203.0.113.0/24`?
3. What is `IPV4_MAX_PREFIXLEN` for, and what verdict fires if `max_length` is 40?
4. `_parse_prefix()` returns `None` on bad input instead of raising. What does `validate_roa()` do with that `None`, and where?
5. `max_length` equal to the prefix's own length (e.g. `/24` prefix, `max_length=24`) — is that valid or invalid? Which comparison operator makes that so?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/rpki/session_01_walkthrough.py
```

The walkthrough builds one well-formed ROA, then breaks it two different ways — an unparseable prefix and two flavors of bad `max_length` — and prints the object itself to show it really is just three fields.

## Done When

The learner can say all of the following without looking at notes:

- "A ROA is three fields: prefix, max_length, origin_asn — nothing else."
- "`max_length` can only narrow the prefix, never widen it, and it caps out at /32 in this IPv4-only toy."
- "`MALFORMED_PREFIX` and `INVALID_MAX_LENGTH` are different failures because they have different remedies."
- "This is the unsigned payload of a real ROA, not a real ROA — no signature, no CA, no IPv6."

## References

- RFC 6482 (A Profile for Route Origin Authorizations, ROAs)
