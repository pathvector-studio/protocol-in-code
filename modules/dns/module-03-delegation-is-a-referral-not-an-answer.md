# Session 03 / Module 03: Delegation Is a Referral, Not an Answer

## Position

- Track: DNS
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/dns/module-03/index.html`
- Source file: `src/protocol_in_code/dns/referral.py`
- Walkthrough script: `examples/dns/session_03_walkthrough.py`

## Core Question

When a server responds, how does the resolver decide whether it just got an answer, a hand-off, or a dead end?

## Outcome

By the end of this session, the learner should be able to:

- classify a response as Answer, Referral, NoData, NameError, or ServerFailure
- explain which message sections drive that classification
- distinguish "the name has no data of this type" from "the name does not exist"
- explain why a referral carries the next servers to ask

## Read Order

1. Read `ResourceRecord` and `ServerResponse`
2. Read `ResponseKind`
3. Read `classify_response()`
4. Read `referral_targets()`
5. Run `examples/dns/session_03_walkthrough.py`
6. For each `ResponseKind`, say what the resolver does next

## Read It Like Code

```python
ServerResponse(
    rcode,
    answer_records,
    authority_ns,
    is_authoritative,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `rcode` | The server's own verdict. NXDOMAIN and SERVFAIL are decided here, before any section is read. |
| `answer_records` | Anything here means the question was answered. |
| `authority_ns` | NS names in the authority section. With no answer and no authority bit, this is a referral. |
| `is_authoritative` | The same empty answer means NoData from an authoritative server and Referral from a parent. |

## Decision Flow

```text
rcode == NXDOMAIN                     -> NameError
rcode != NOERROR                      -> ServerFailure
answer section has records           -> Answer
authority NS set, not authoritative  -> Referral
otherwise                            -> NoData
```

## Reading Lens

The important move in this session is to stop reading a DNS response as "did I get an IP?" and start asking:

- which branch of `classify_response()` did this response take?
- which field flipped the classification?
- what is the next action this classification implies?

## Toy Model Boundary

Real responses carry counts, flags, and additional-section glue. This lesson keeps only the fields the classification logic actually branches on. That is the point: five outcomes, four fields.

`referral_targets()` returns server names, not addresses. Resolving those names (glue) is real-world work this toy skips.

## Code Landmarks

### `ResponseKind`

Five named outcomes. Every response a resolver ever receives lands in exactly one of them.

### `classify_response()`

The main reading target. The order of the branches matters: rcode is checked before sections, answer before authority.

### `referral_targets()`

A referral is only useful because it names who to ask next. For any other kind, the next-server list is empty by construction.

## Failure Questions

Use the source file to answer these:

1. Why is NXDOMAIN checked before the answer section is examined?
2. Two responses both have an empty answer section and NS records in authority. One is NoData, one is Referral. Which field differs?
3. What does `referral_targets()` return for an Answer, and why is that the safe behavior?
4. Why is NoData not a failure?
5. Which `ResponseKind` values should make the resolver try a different server?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dns/session_03_walkthrough.py
```

The walkthrough classifies five responses and shows that only the referral yields next servers.

## Done When

The learner can say all of the following without looking at notes:

- "A referral is an empty answer plus authority NS from a non-authoritative server."
- "NoData means the name exists but has no records of this type. NXDOMAIN means the name does not exist."
- "Classification comes first. What to do next follows from the kind, not from the raw packet."

## References

- RFC 1034 Section 4.3.1
- RFC 2308 Section 1 (NODATA and NXDOMAIN)
- RFC 8499 (referral terminology)
