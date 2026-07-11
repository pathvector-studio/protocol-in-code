# Session 04 / Module 04: Validation Walks Up the Tree

## Position

- Track: DNSSEC
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/dnssec/module-04/index.html`
- Source file: `src/protocol_in_code/dnssec/chain.py`
- Walkthrough script: `examples/dnssec/session_04_walkthrough.py`

## Core Question

A signed answer arrives with an RRSIG attached. What exact sequence of checks turns that into SECURE, one of three flavors of BOGUS, or INSECURE — and why does the walk go up, not down?

## Outcome

By the end of this session, the learner should be able to:

- name the five possible `ChainOutcome` values `validate_chain()` can return
- trace the hop order: record RRSIG under the ZSK, DNSKEY rrset under the KSK, KSK hash against the parent's DS, repeated zone by zone to the root
- explain why a missing DS entry is INSECURE, not BOGUS, and why that distinction is structural rather than a judgment call
- state what the trust anchor actually is — a `Ds`, not a key

## Read Order

1. Read the module comment at the top of `chain.py` contrasting this walk with `tls/chain.py`
2. Read `ChainOutcome`
3. Read `ZoneData`
4. Read `_zone_chain()`
5. Read `validate_chain()` top to bottom
6. Run `examples/dnssec/session_04_walkthrough.py`

## Read It Like Code

```python
ZoneData(
    zone,
    keys,
    key_rrsig,
    ds_for_children,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `zone` | The zone this data belongs to. `""` names the root zone. |
| `keys` | The zone's KSK and ZSK, held together as one tuple. `_find_key()` picks the one the current step needs. |
| `key_rrsig` | The KSK's signature over this zone's own DNSKEY rrset — the key signs the key. |
| `ds_for_children` | A dict keyed by child zone name. A child with no entry here is not "broken" — it is unsigned, and that absence is the whole INSECURE branch. |

## Decision Flow

```text
no ZoneData for the record's own zone       -> INSECURE
no ZSK on file for that zone                -> INSECURE
record's RRSIG fails to verify under ZSK    -> BOGUS_RECORD_SIG
  ... then for each zone from owner up to root:
no ZoneData for this zone                   -> INSECURE
no KSK on file for this zone                -> INSECURE
DNSKEY rrset's RRSIG fails under KSK        -> BOGUS_KEY_SIG
zone is root and KSK doesn't hash to anchor -> BOGUS_DS_MISMATCH
zone is root and KSK does hash to anchor    -> SECURE (stop)
no ZoneData for the parent zone             -> INSECURE
parent has no DS entry for this zone        -> INSECURE
DS entry exists but doesn't hash to KSK     -> BOGUS_DS_MISMATCH
DS entry hashes to KSK                      -> continue up to the parent
```

## Reading Lens

The important move in this session is to stop thinking of DNSSEC validation as "checking a signature" and start asking, at every hop:

- which key is verifying which signature right now — the ZSK over the record, or the KSK over the DNSKEY rrset?
- is this hop comparing a signature, or comparing a hash (KSK against DS)? They are different operations and different failure flavors.
- has the walk reached the root yet? Every hop before the root looks up a DS in the *parent*; the root hop compares against `trust_anchor` instead, because the root has no parent to ask.

Contrast this against Session 04 of the TLS track (`tls/chain.py`, "Trust Is a Walk Up the Chain"). Both walks climb from a leaf fact to something already trusted, hop by hop, and both are string/hash comparisons rather than real cryptography. But the shapes differ: TLS's chain is a list of certificates that can terminate at *any* root sitting in a local trust store — many valid roots, chosen by whichever issuer happened to sign the leaf. DNSSEC's chain is zone-cut hops within *one* tree — child, parent, grandparent, up to the root — and there is exactly one anchor: the root's key, pinned once as `trust_anchor`. There is nowhere else the DNSSEC walk can end up. Where TLS asks "is the last cert's issuer in my trust store?", DNSSEC asks "does this walk reach the one root I already know?"

## Toy Model Boundary

Real DNSSEC proves that an unsigned delegation is real — not just missing from the resolver's view — with an NSEC or NSEC3 record over the parent's namespace (RFC 4035 §5.4). This toy has no such proof: an absent `ds_for_children` entry is trusted at face value as "this child was never signed." That is an honest simplification, not a shortcut around a hard case — the toy's point is the structural shape of the walk, not authenticated denial of existence.

This module also carries no signature algorithms, no algorithm negotiation, and no key rollover. `verify_rrsig()` (Session 01) and `ds_matches()` (Session 03) are sha256 comparisons standing in for real cryptography; nothing here proves a signature was ever produced with a private key. Time is an integer `now` passed as an argument, exactly like the DNS and TLS tracks' toy clocks.

The record fed into `validate_chain()` is handed in fully formed — an `Rrset` and its covering `Rrsig`, already fetched. Session 05 wraps that with a name/type check, but resolution itself (walking the DNS tree to find the record in the first place) is the DNS track's job, not this one's.

## Code Landmarks

### The module comment at the top of `chain.py`

The clearest statement in the whole track of why DNSSEC's walk and TLS's walk look similar but aren't. Read it before reading `validate_chain()`.

### `_zone_chain()`

`"example.com"` becomes `["example.com", "com", ""]`. This is the walk order made explicit as a list — `validate_chain()`'s loop iterates exactly this sequence, one DNSKEY/KSK/DS check per entry.

### The record-signature check, before the loop even starts

```python
record_outcome = verify_rrsig(rrset, rrsig, zsk.key_secret, now)
if record_outcome is not VerifyOutcome.OK:
    ...
    return ChainResult(ChainOutcome.BOGUS_RECORD_SIG, tuple(trace))
```

This runs once, against the *record's own* zone's ZSK, before the walk up to the root even begins. Every other check inside the loop verifies a DNSKEY rrset's signature or a DS hash — never the original record again.

### The root case inside the loop

```python
if zone_name == "":
    if not ds_matches(trust_anchor, ksk):
        ...
        return ChainResult(ChainOutcome.BOGUS_DS_MISMATCH, ...)
    ...
    return ChainResult(ChainOutcome.SECURE, ...)
```

The root zone is the one place in the loop that does not look up a parent's DS — there is no parent. Instead the root's KSK is hashed and compared straight against `trust_anchor`, which is a `Ds`, not a `DnsKey`. This is the only path in the function that returns `SECURE`.

### The missing-DS branch

```python
ds = parent.ds_for_children.get(zone_name)
if ds is None:
    trace.append(f"{parent_name}: no DS on file for {zone_name}")
    return ChainResult(ChainOutcome.INSECURE, tuple(trace))
```

This fires *before* `ds_matches()` is ever called. INSECURE is reached by a dictionary lookup returning `None` — structurally impossible to confuse with a failed comparison, because no comparison ran.

## Failure Questions

Use the source file to answer these:

1. `validate_chain()` calls `verify_rrsig()` against the record's own zone ZSK once, outside the `_zone_chain()` loop. Which key verifies the DNSKEY rrset's signature at every zone visited *inside* the loop — is it the same key role, or a different one?
2. For a record owned by `example.com`, list the zones `_zone_chain()` produces and, for each one, name the single check that must pass before the walk advances to the next zone.
3. `validate_chain()` never calls `ds_matches()` for the root zone's own entry. What does it compare the root's KSK against instead, and what type is that value — a `DnsKey` or a `Ds`?
4. If `com`'s `ds_for_children` dict has no entry for `"example.com"`, which line of `validate_chain()` returns first, and does `verify_rrsig()` or `ds_matches()` run at all for that hop?
5. Two different failures both produce `BOGUS_DS_MISMATCH`: one at the root and one at a non-root zone. What is different about what each one compares the KSK against?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dnssec/session_04_walkthrough.py
```

The walkthrough builds the demo tree (`root -> com -> example.com`, fully signed) and validates it SECURE with a trace ending on the trust-anchor match, then breaks it three ways: `tamper_record()` swaps the answer after signing (BOGUS_RECORD_SIG), `tamper_ds()` points `com`'s DS at the wrong key (BOGUS_DS_MISMATCH), and `unsign_child()` deletes `com`'s DS entry for `example.com` entirely (INSECURE) — and confirms that last trace has no signature-failure line in it, because no signature check ever ran.

## Done When

The learner can say all of the following without looking at notes:

- "The walk goes record -> ZSK -> DNSKEY rrset -> KSK -> parent's DS -> repeat, until a KSK matches the trust anchor."
- "The trust anchor is a Ds — a fingerprint — not a key. The root's KSK is proven by hashing to it, the same operation used at every other hop."
- "INSECURE from a missing DS entry is structural: the code returns before any signature or hash comparison runs, because there is nothing to compare."
- "DNSSEC has one tree and one anchor; TLS has one trust store and many possible roots. Same walk shape, different topology."

## References

- RFC 4033 (DNS Security Introduction and Requirements — architecture framing for the chain of trust)
- RFC 4035 Section 5 (Authenticating DNS Responses), Section 5.4 (Authenticated Denial of Existence — the NSEC/NSEC3 proof this toy skips)
