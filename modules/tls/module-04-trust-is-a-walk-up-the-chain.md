# Session 04 / Module 04: Trust Is a Walk Up the Chain

## Position

- Track: TLS
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/tls/module-04/index.html`
- Source file: `src/protocol_in_code/tls/chain.py`
- Walkthrough script: `examples/tls/session_04_walkthrough.py`

## Core Question

A server hands you a stack of certificates. What exactly turns that stack into a single yes/no answer, and in what order do the checks run?

## Outcome

By the end of this session, the learner should be able to:

- name the six possible verdicts `verify_chain()` can return
- explain why validity windows are checked before issuer links
- explain what makes a single self-signed root a valid chain of length one
- describe exactly what "untrusted root" means versus "broken chain"

## Read Order

1. Read `ChainVerdict`
2. Read `Certificate`
3. Read `verify_chain()` top to bottom
4. Run `examples/tls/session_04_walkthrough.py`

## Read It Like Code

```python
Certificate(
    subject,
    issuer,
    public_key_id,
    not_before,
    not_after,
    is_ca,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `subject` | The identity this certificate vouches for. Must equal the next cert's `issuer` for the chain to link. |
| `issuer` | Who signed this certificate. The chain is a walk from `subject` to `issuer`, cert by cert. |
| `not_before` / `not_after` | The validity window. Checked for every certificate in the chain, not just the leaf. |
| `is_ca` | Present on every `Certificate` but not read by `verify_chain()` — the toy model trusts chain order, not this flag. |
| `public_key_id` | Carried along but only compared implicitly through `trust_store` lookups by name, not by key. |

## Decision Flow

```text
chain is empty                                  -> EmptyChain
any cert: now < not_before                       -> NotYetValid
any cert: now >= not_after                       -> Expired
any adjacent pair: current.issuer != next.subject -> BrokenChain
last cert's issuer not in trust_store             -> UntrustedRoot
otherwise                                         -> Trusted
```

## Reading Lens

The important move in this session is to stop thinking of "chain validation" as one big check and start asking:

- which certificates get their window checked — all of them, or just the leaf?
- which pair of certs is being compared when a link check runs?
- whose `issuer` is looked up in `trust_store` — the leaf's, or the last cert's?

## Toy Model Boundary

Real chain validation checks cryptographic signatures (does the issuer's public key actually sign the subject's certificate?) and consults revocation status (CRL/OCSP). This toy model checks none of that: it only compares `subject`/`issuer` strings and integer time windows. A chain that "links" here is a chain where the names match — nothing here proves a signature was ever produced or verified.

Time is an abstract integer tick, passed as `now`, exactly like the DNS track's cache. There is no wall clock inside `verify_chain()`.

## Code Landmarks

### `ChainVerdict`

Six outcomes, and the order they're listed in the enum is not the order they're checked in — read `verify_chain()` for the real order, not the enum.

### The first loop: validity windows

```python
for cert in chain:
    if now < cert.not_before:
        return ChainVerdict.NOT_YET_VALID
    if now >= cert.not_after:
        return ChainVerdict.EXPIRED
```

This runs over **every** certificate in the chain before any link is checked. A validity failure anywhere in the chain — root, intermediate, or leaf — short-circuits before `BrokenChain` or `UntrustedRoot` ever get a chance.

### The second loop: pairwise links

```python
for position in range(len(chain) - 1):
    current = chain[position]
    next_cert = chain[position + 1]
    if current.issuer != next_cert.subject:
        return ChainVerdict.BROKEN_CHAIN
```

`range(len(chain) - 1)` means a chain of length 1 — a single self-signed root — skips this loop entirely. There is nothing to pair it with, so it cannot be broken by this check.

### The trust store check

```python
last = chain[-1]
if trust_store.get(last.issuer) is None:
    return ChainVerdict.UNTRUSTED_ROOT
```

Only the **last** certificate's `issuer` is looked up. For a single self-signed root, `chain[-1]` is the root itself, so its own `issuer` (itself, if self-signed) must be a key in `trust_store`.

## Failure Questions

Use the source file to answer these:

1. At exactly `now == cert.not_after`, which verdict fires, and which comparison operator (`<`, `<=`, `>=`, `>`) decides it?
2. If the leaf certificate is expired *and* the chain also has a broken issuer link, which verdict does `verify_chain()` return, and why does the order of the two loops guarantee that?
3. For a chain of exactly one self-signed certificate, why does `BROKEN_CHAIN` never fire regardless of what `subject`/`issuer` contain?
4. Whose `issuer` field is checked against `trust_store` — the leaf's or the root's — and what would happen if you accidentally checked the leaf's instead?
5. Does `verify_chain()` ever read `is_ca`? What does that tell you about what this toy model does and does not enforce?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tls/session_04_walkthrough.py
```

The walkthrough builds a trusted leaf-intermediate-root chain, then breaks it one dimension at a time: a mismatched issuer, an expired window (checked at exactly `not_after`), a not-yet-valid window, a root missing from `trust_store`, and an empty chain.

## Done When

The learner can say all of the following without looking at notes:

- "Every certificate's validity window is checked before any issuer link is checked."
- "A chain of length one skips the pairwise loop entirely — there's nothing to compare it to."
- "Untrusted root and broken chain are different failures: one is about names matching between certs, the other is about the last cert's issuer not being a known root."
- "This is string and integer comparison, not cryptography — no signature is verified here."

## References

- RFC 5280 Section 6.1 (path validation, simplified — this toy model skips signature verification and policy processing)
- RFC 8446 Section 4.4.2 (Certificate message: how the chain arrives at the peer)
