# Session 03 / Module 03: DS Links Child to Parent

## Position

- Track: DNSSEC
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/dnssec/module-03/index.html`
- Source file: `src/protocol_in_code/dnssec/ds.py`
- Walkthrough script: `examples/dnssec/session_03_walkthrough.py`

## Core Question

A resolver trusts the parent zone. The child zone hands it a KSK it has never seen before. What one fact lets the resolver decide to trust that key too?

## Outcome

By the end of this session, the learner should be able to:

- state which three fields make up a `Ds` record and why that's all it needs
- explain what `ds_digest()` actually hashes, and why a KSK (not a ZSK) is the input
- explain why the DS record lives in the parent zone rather than the child
- trace `ds_matches()` and explain each of its three comparisons

## Read Order

1. Read the module docstring at the top of `ds.py`
2. Read `Ds`
3. Read `ds_digest()`
4. Read `make_ds()` and its docstring
5. Read `ds_matches()`
6. Run `examples/dnssec/session_03_walkthrough.py`

## Read It Like Code

```python
Ds(
    child_zone,
    key_tag,
    digest,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `child_zone` | Which zone this DS record delegates trust to. Checked first in `ds_matches()`. |
| `key_tag` | The candidate key's tag (Session 02), letting a resolver shortlist which DNSKEY record this DS is even talking about before hashing anything. |
| `digest` | The fingerprint of the child's KSK. This is the one field that actually proves the key is the right key. |

## Decision Flow

```text
make_ds(child_ksk):
  child_ksk.role != KSK  -> raise ValueError (a DS record digests a KSK, not a ZSK)
  otherwise               -> Ds(child_zone=child_ksk.zone, key_tag=child_ksk.key_tag, digest=ds_digest(child_ksk))

ds_matches(ds, key):
  ds.child_zone == key.zone
  and ds.key_tag == key.key_tag
  and ds.digest == ds_digest(key)   -> True only if all three hold
```

## Reading Lens

`Ds` is deliberately small — three facts, no signature, no validity window of its own. Read it against the thesis stated directly in `make_ds()`'s docstring: the parent zone stores a FINGERPRINT of the child's KSK. That fingerprint is the one cross-zone fact that stitches the DNS tree together. It is data in the *parent*, served alongside the delegation to the child — not something the child has to push out-of-band through some separate introduction channel. A resolver that already trusts the parent's signed answers (Session 01) can extend that trust to the child's KSK the moment the child's DNSKEY rrset hashes to match this DS record.

Read `ds_digest()` next and notice exactly what goes into the hash: `zone`, `key_tag`, and `key_secret` — all three, concatenated. That means the same secret under a different zone name produces a different digest (the fingerprint is bound to *this* zone owning *this* key), and `ds_matches()` additionally checks `child_zone` and `key_tag` directly before ever recomputing the digest — a deliberate short-circuit, the same "cheap checks before the hash" shape `verify_rrsig()` used in Session 01.

## Toy Model Boundary

A real DS digest is SHA-256 over the owner name and the wire-encoded DNSKEY RDATA (RFC 4509) — a specific byte-level encoding of the actual key material, not a Python string. This toy instead hashes `f"{zone}|{key_tag}|{key_secret}"`: same idea (fingerprint some canonical representation of the key), no wire format, no cryptographic strength claim. There is also no support here for multiple digest algorithms (RFC 4509 defines more than one), no key rollover timing, and `make_ds()`'s `role is not KeyRole.KSK` check is the toy's entire enforcement of "a DS record digests a KSK, not a ZSK" — real deployments rely on operational convention plus the protocol's structure, not a runtime guard.

## Code Landmarks

### `ds_digest()`

The whole fingerprint in one line: `sha256(f"{key.zone}|{key.key_tag}|{key.key_secret}")`. Every one of those three inputs matters — change any one and the digest changes.

### `make_ds()`

Reading target. The `role` check comes first, as a hard `ValueError` — this function refuses to even construct a `Ds` for a ZSK. Read the docstring's last sentence carefully: "no separate out-of-band introduction needed." That is the payoff for the whole chain from Session 01 through here.

### `ds_matches()`

Three `and`-ed comparisons, all of which must hold. `child_zone` and `key_tag` are cheap equality checks; `digest` is the one that actually requires recomputing a hash over the candidate key.

## Failure Questions

Use the source file to answer these:

1. What three values does `ds_digest()` concatenate before hashing, and in what order?
2. `make_ds()` raises `ValueError` if the key's role isn't `KSK`. What is the source's own stated reason a DS record digests a KSK and not a ZSK — where does that reasoning live, and what would break if a ZSK's fingerprint were published in the parent instead?
3. Two `DnsKey` values share the same `key_secret` but have different `zone` values. Do they produce the same `key_tag`? Do they produce the same `ds_digest()`? Explain the difference by pointing at exactly which function reads which field.
4. `ds_matches()` checks `child_zone`, `key_tag`, and `digest`, all three, with `and`. Construct a scenario (in words) where `key_tag` matches but `digest` does not — what would have to be different about the candidate key?
5. Why does `Ds` itself carry no `inception`/`expiration` fields the way `Rrsig` does? What in `make_ds()`'s docstring explains what "trusting" a DS record actually depends on instead?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dnssec/session_03_walkthrough.py
```

The walkthrough builds a DS record from a child KSK, confirms `ds_matches()` returns True for that same key, then False for a different key entirely, then False again for a key that shares the same secret but belongs to a different zone — proving the digest is bound to the zone, not just the secret. It closes by reading the `Ds` object's three fields directly.

## Done When

The learner can say all of the following without looking at notes:

- "A DS record is a fingerprint of the child's KSK, stored as data in the parent zone."
- "`ds_digest()` hashes the zone, the key tag, and the key secret together — the same secret under a different zone produces a different digest."
- "`ds_matches()` is three comparisons, all required: zone, key tag, then the recomputed digest."

## References

- RFC 4033 (DNS Security Introduction and Requirements) — how the DS record extends trust from parent to child
- RFC 4034 Section 5 (DS RR) — record format
- RFC 4509 — the SHA-256 DS digest type this module's `ds_digest()` stands in for
