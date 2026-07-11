# Session 01 / Module 01: A Signature Rides Beside the Record

## Position

- Track: DNSSEC
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/dnssec/module-01/index.html`
- Source file: `src/protocol_in_code/dnssec/rrsig.py`
- Walkthrough script: `examples/dnssec/session_01_walkthrough.py`

## Core Question

A resolver receives an answer from a cache that has never talked to the authoritative server. What makes that answer trustworthy anyway?

## Outcome

By the end of this session, the learner should be able to:

- explain why the signature is data stored in the zone, not a property of the connection it arrived on
- name every input that goes into the toy signature
- state the difference between `EXPIRED` and `NOT_YET_VALID`
- explain why a signature that is otherwise perfect still fails when checked against a different name

## Read Order

1. Read the module docstring at the top of `rrsig.py` (the TLS contrast)
2. Read `VerifyOutcome`
3. Read `Rrset` and `Rrsig`
4. Read `_signature_material()`
5. Read `sign_rrset()`
6. Read `verify_rrsig()` top to bottom
7. Run `examples/dnssec/session_01_walkthrough.py`

## Read It Like Code

```python
Rrsig(
    covered_name,
    covered_type,
    signer,
    key_tag,
    signature,
    inception,
    expiration,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `covered_name` / `covered_type` | The exact rrset this signature claims to cover. `verify_rrsig()` checks these before anything else. |
| `signer` | The zone that produced this signature — carried along, not itself checked by `verify_rrsig()`. |
| `key_tag` | Identifies which key signed this, without carrying the key material. |
| `signature` | The toy sha256 hexdigest. Recomputed by the verifier, never trusted as-is. |
| `inception` / `expiration` | The validity window. Both bounds are checked against `now` before the signature itself is recomputed. |

## Decision Flow

```text
rrset.name/rtype != rrsig.covered_name/covered_type -> WrongName
now < rrsig.inception                                -> NotYetValid
now >= rrsig.expiration                               -> Expired
recomputed signature != rrsig.signature               -> BadSignature
otherwise                                              -> Ok
```

## Reading Lens

The move this session asks for is to stop picturing DNSSEC as "TLS for DNS" and read the actual contrast the source states outright: TLS protects the pipe — the handshake authenticates a connection, and the guarantee ends when the connection does. DNSSEC signs the *contents*. The `Rrsig` is data sitting in the zone right next to the `Rrset` it covers. It is cacheable, forwardable, and servable by any resolver in the chain, and it is valid no matter who handed it to you — a cache that has never spoken to the authoritative server can still hand out a signed answer a stub resolver can verify on its own.

Read `verify_rrsig()` with that lens: every input it needs — the `rrset`, the `rrsig`, and the `key_secret` — is either data already in hand or a key looked up separately. Nothing about the network path the answer took enters the computation at all.

## Toy Model Boundary

Real DNSSEC signs with RSA or ECDSA over a canonical wire encoding of the rrset (RFC 4034 SS3.1.8.1), where record ordering and encoding are strictly defined so every implementation hashes the same bytes. This toy replaces all of that with a single sha256 hexdigest over `(key_secret, name, rtype, sorted records, inception, expiration)` — same idea, no cryptographic strength claim, and no wire format. `sorted(records)` stands in for canonical ordering; it isn't the real algorithm, but it captures why order can't be allowed to matter to the signature. Anyone who knows `key_secret` can forge a valid-looking signature here, which is exactly why this file exists as a toy: it isolates the *shape* of "recompute and compare" from the cryptography that makes it actually hard to forge.

## Code Landmarks

### `_signature_material()`

The one function that decides what "the signature" is actually over. Note that `inception` and `expiration` are baked into the material — change either one and the signature no longer matches, even if the rrset is untouched.

### `sign_rrset()`

Produces a signature once, over the rrset and its validity window, then the `Rrsig` travels with the data from then on. Nothing about signing touches a network call.

### `verify_rrsig()`

The main reading target. Four early-exit checks before a single hash is computed: name/type match, then the two time bounds, then — only if all three pass — the signature is recomputed and compared.

## Failure Questions

Use the source file to answer these:

1. What five things go into `_signature_material()`, and what happens to the signature if the record list is the same set but written in a different order?
2. `verify_rrsig()` checks `now < rrsig.inception` for `NOT_YET_VALID` and `now >= rrsig.expiration` for `EXPIRED`. At `now == expiration` exactly, which branch fires, and why is the comparison `>=` and not `>`?
3. Why does changing a single record in the `Rrset` passed to `verify_rrsig()` produce `BAD_SIGNATURE` rather than some other outcome?
4. `verify_rrsig()` checks `covered_name`/`covered_type` before checking the time window. What would go wrong (or what would the returned outcome mean) if that order were reversed?
5. The docstring on `verify_rrsig()` says "the only inputs a verifier ever needs are the rrset and the key." List every parameter `verify_rrsig()` actually takes, and explain which of them count as "the key" and which don't.

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dnssec/session_01_walkthrough.py
```

The walkthrough signs one rrset and then verifies it five different ways: a clean verify, a tampered record, exactly at expiration, before inception, and against a different name. The headline: the signature rode beside the data and survived the trip only if the data did.

## Done When

The learner can say all of the following without looking at notes:

- "DNSSEC signs the contents, not the connection — the signature is data that lives in the zone."
- "A verifier needs the rrset, the rrsig, and the key secret. Nothing about how the answer arrived matters."
- "Name/type mismatch, then the time window, then the recomputed hash — in that order, before `OK` is possible."

## References

- RFC 4033 (DNS Security Introduction and Requirements) — the architecture this module is one piece of
- RFC 4034 Section 3 (RRSIG RR) — record format and the canonical signing procedure this toy stands in for
