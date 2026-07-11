# Session 07 / Module 07: The Record Layer Is an Envelope

## Position

- Track: TLS
- Session: 07
- Site lesson: `pathvector-site/courses/protocols-in-code/tls/module-07/index.html`
- Source file: `src/protocol_in_code/tls/record.py`
- Walkthrough script: `examples/tls/session_07_walkthrough.py`

## Core Question

What does a TLS record actually protect, what stays visible on the outside, and what does "the tag doesn't match" tell you versus what it doesn't tell you?

## Outcome

By the end of this session, the learner should be able to:

- name the two fields on `Record` that ride outside the seal, and the two that are sealed
- explain what the integrity tag is computed over, and why the sequence number is part of that computation
- state the one failure outcome `unprotect()` can actually return, and which three distinct real-world causes all collapse into it
- explain why this collapse is a deliberate design choice, not a missing feature

## Read Order

1. Read the module comment at the top of the file
2. Read `Record`
3. Read `UnprotectOutcome` and `UnprotectResult`
4. Read `_tag_for()`
5. Read `protect()`
6. Read `unprotect()`
7. Run `examples/tls/session_07_walkthrough.py`

## Read It Like Code

```python
Record(
    content_type,
    seq,
    ciphertext,
    tag,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `content_type` | Rides outside the seal. A record's kind (handshake, application data, alert) is visible before the record is opened. |
| `seq` | Rides outside the seal, but is folded into the tag computation. Visible, and also load-bearing for integrity. |
| `ciphertext` | In this toy, the plaintext left readable — see Toy Model Boundary. In real TLS this is the encrypted payload. |
| `tag` | The seal itself: a sha256 hash over `(key, seq, plaintext)`. Recomputing it is the only way to open a record. |

## Decision Flow

```text
unprotect(record, key):
  expected = tag_for(key, record.seq, record.ciphertext)
  record.tag != expected  -> BAD_TAG, plaintext=None
  record.tag == expected  -> OK, plaintext=record.ciphertext
```

## Reading Lens

The important move in this session is to stop thinking of "encrypted" and "authenticated" as two separate guarantees and start asking:

- what is visible on a `Record` before you ever call `unprotect()`?
- what three inputs feed `_tag_for()`, and what happens to the tag if any one of them changes?
- when `unprotect()` returns `BAD_TAG`, which of those three inputs was wrong? Can you tell from the outcome alone?

## Toy Model Boundary

Real TLS protects records with an AEAD cipher (e.g. AES-GCM) that both encrypts and authenticates in one step. Here the "ciphertext" is the plaintext left readable, and the integrity tag is a sha256 hash over `(key, seq, plaintext)`. That keeps the envelope metaphor honest without pretending to be real cryptography — the module comment says so directly, and this lesson repeats it rather than hiding it.

`content_type` is never encrypted in this toy model either. Real TLS 1.3 hides the true content type inside the encrypted payload and puts a fixed `application_data` type on the wire (RFC 8446 SS5.1); this module keeps `content_type` in the clear on `Record` so the envelope's "outside vs. inside" boundary stays easy to read at a glance.

## Code Landmarks

### The module comment

States the toy substitution before any code does. Read this before `Record`, not after.

### `_tag_for()`

Three inputs, one hash: `key`, `seq`, `plaintext`. Every other function in this file is a thin wrapper around calling this and comparing.

### `protect()`

The docstring says it plainly: sealing a record binds its sequence number into the tag, so replay or reorder breaks it too. There is no separate sequence-number check anywhere in this file — `seq` is enforced entirely through the tag.

### `unprotect()`

The reading target. One `if`, one comparison, two possible outcomes — `OK` or `BAD_TAG`. `UnprotectOutcome` declares a third value, `WRONG_KEY`, that this function never returns.

## Failure Questions

Use the source file to answer these:

1. `UnprotectOutcome` declares `WRONG_KEY` as a value. Under what condition does `unprotect()` actually return it?
2. If you call `unprotect()` with the right key but the wrong `seq`, what outcome do you get, and which line of `_tag_for()` explains why?
3. Two records have the same `ciphertext` and `tag` but different `seq`. Can both successfully `unprotect()` with the same key? Trace through `_tag_for()` to justify your answer.
4. Does `content_type` ever appear inside the material hashed by `_tag_for()`? What does that imply about tampering with `content_type` alone?
5. `protect()` takes `content_type` as a keyword argument with a default. What is that default, and where does `run_handshake()` (Session 09) rely on it?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tls/session_07_walkthrough.py
```

The walkthrough seals one record and opens it, then breaks the seal three different ways — tampered ciphertext, wrong key, wrong sequence number — and shows that all three land on the same `BAD_TAG` outcome with `plaintext=None`. A final scenario protects a second record at the next sequence number to show each seal stands on its own.

## Done When

The learner can say all of the following without looking at notes:

- "content_type and seq ride on the outside of the envelope; the tag seals the inside, and seq is baked into the tag anyway."
- "BAD_TAG is the only failure this function returns — tampering, the wrong key, and a replayed sequence number are indistinguishable from the caller's side."
- "That collapse is intentional: revealing which one failed would leak information to an attacker probing the channel."

## References

- RFC 8446 Section 5.1 (Record Layer)
- RFC 8446 Section 5.2 (Record Payload Protection)
