# Session 02 / Module 02: The Key Signs the Key

## Position

- Track: DNSSEC
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/dnssec/module-02/index.html`
- Source file: `src/protocol_in_code/dnssec/dnskey.py`
- Walkthrough script: `examples/dnssec/session_02_walkthrough.py`

## Core Question

A zone publishes two keys. Why two, and what exactly does each one sign?

## Outcome

By the end of this session, the learner should be able to:

- name the two key roles and state which one signs which kind of rrset
- explain why the DNSKEY rrset contains both keys instead of one record per key
- explain why the ZSK can rotate without contacting the parent zone, while the KSK cannot
- trace `derive_key_tag()` and explain why it is deterministic

## Read Order

1. Read the module docstring at the top of `dnskey.py`
2. Read `KeyRole`
3. Read `DnsKey`
4. Read `derive_key_tag()`
5. Read `make_key()`
6. Read `key_rrset()`
7. Read `sign_key_rrset()` and its docstring
8. Run `examples/dnssec/session_02_walkthrough.py`

## Read It Like Code

```python
DnsKey(
    zone,
    role,
    key_secret,
    key_tag,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `zone` | Which zone this key belongs to. Both KSK and ZSK for a zone share this value. |
| `role` | `KSK` or `ZSK` — the source enforces different responsibilities per role, not just a label. |
| `key_secret` | The toy stand-in for key material. Whoever holds it can sign as this key. |
| `key_tag` | Derived from `key_secret` by `derive_key_tag()`, never chosen independently — see `make_key()`. |

## Decision Flow

```text
key_rrset(zone, keys)          -> one Rrset, name=zone, rtype=DNSKEY, one record per key
sign_key_rrset(keys, ksk, ...) -> sign_rrset() called with the KSK's own secret and key_tag,
                                   over the rrset that contains BOTH keys
ordinary rrset (A, MX, ...)    -> signed by the ZSK, via sign_rrset() directly (session 01)
```

## Reading Lens

The reading target this session is the self-reference: the KSK does not sign itself in isolation, and it does not sign the ZSK in isolation. `sign_key_rrset()` builds one `Rrset` via `key_rrset()` that contains *both* keys as records, and the KSK signs that combined rrset. Read `key_rrset()` first and notice it treats keys the same way `rrsig.py` treats any other answer — `role.value:key_tag` strings, nothing more — before `sign_key_rrset()` does anything key-specific to it.

Then ask why this buys anything. The docstring on `sign_key_rrset()` states it directly: splitting the role in two lets the ZSK rotate on its own schedule. A new ZSK just needs a fresh KSK signature over the (updated) DNSKEY rrset — a fact entirely local to this zone. The KSK, by contrast, changes rarely, because rolling it means updating the DS record one level up in the parent zone (Session 03). Two tiers exist so that the frequent operation (ZSK rotation) and the rare, cross-zone operation (KSK rollover) don't have to happen on the same schedule.

## Toy Model Boundary

Real DNSKEY records carry an algorithm identifier and public key material (RFC 4034 SS2.1), and the key tag is a checksum computed over that wire-encoded record (RFC 4034 Appendix B) — a real implementation detail with edge cases the checksum was specifically designed around. This toy replaces the wire encoding with a plain string (`key_secret`) and computes `key_tag` as `sha256(key_secret) mod 65536`. It is deterministic and collision-shy enough to read cleanly in a walkthrough, but it makes no claim to match the real RFC 4034 Appendix B algorithm, and there is no algorithm identifier, no public/private key distinction, and no actual asymmetric cryptography anywhere in this module.

## Code Landmarks

### `derive_key_tag()`

One line of real content: hash the secret, fold into 16 bits. Called from `make_key()`, never handed in by the caller — that's what "deterministic" buys: two calls with the same secret always produce the same tag, so a KSK and a re-derived copy of it agree without coordination.

### `key_rrset()`

Turns a tuple of `DnsKey` into an ordinary `Rrset` with `rtype="DNSKEY"`. This is the moment the keys stop being "the trust infrastructure" and become "just another answer a zone serves" — the same `Rrset` type from Session 01, subject to the same signing and verification machinery.

### `sign_key_rrset()`

Reading target. Notice the arguments passed to `sign_rrset()`: `ksk.key_secret` and `ksk.key_tag` — always the KSK's, never the ZSK's, regardless of how many keys are in the `keys` tuple. This is the one place "which key signs" is decided in code.

## Failure Questions

Use the source file to answer these:

1. `key_rrset()` builds one record per key as `f"{key.role.value}:{key.key_tag}"`. If a zone has one KSK and one ZSK, how many records does the resulting `Rrset` have, and what does `key_rrset()` alone (without `sign_key_rrset()`) tell you about which key is which role?
2. `sign_key_rrset(keys, ksk, ...)` takes both a `keys` tuple and a separate `ksk` argument. What would it mean, in terms of the resulting `Rrsig`, if `ksk` were not one of the entries in `keys`?
3. Trace `derive_key_tag("some-secret")` by hand: what are the two operations applied to the sha256 hexdigest before it becomes `key_tag`?
4. The docstring on `sign_key_rrset()` says a ZSK rotation "just needs a fresh KSK signature over the DNSKEY rrset, not a new fact in the parent zone." What in `sign_key_rrset()`'s signature (the Python kind — its parameters) supports that claim: does it take any argument that would require contacting a party outside this zone?
5. If `verify_rrsig()` (Session 01) is called on the DNSKEY rrset using the ZSK's `key_secret` instead of the KSK's, which `VerifyOutcome` results, and why — walk through what `_signature_material()` produces in each case.

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dnssec/session_02_walkthrough.py
```

The walkthrough derives a key tag twice to show determinism, builds a two-key DNSKEY rrset, signs it with the KSK, verifies that signature with the KSK secret (passes) and the ZSK secret (fails) — the role-separation headline — then signs and verifies an ordinary rrset with the ZSK directly.

## Done When

The learner can say all of the following without looking at notes:

- "The KSK signs the DNSKEY rrset, which contains both the KSK and the ZSK. The ZSK signs everything else."
- "A key's tag is derived from its secret, not assigned — the same secret always produces the same tag."
- "Two tiers exist so the ZSK can rotate on the zone's own schedule, without touching anything in the parent."

## References

- RFC 4033 (DNS Security Introduction and Requirements) — why the KSK/ZSK split exists
- RFC 4034 Section 2 (DNSKEY RR) — record format and the key tag algorithm this module stands in for
