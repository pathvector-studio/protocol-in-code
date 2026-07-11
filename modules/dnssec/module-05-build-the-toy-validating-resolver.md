# Session 05 / Module 05: Build the Toy Validating Resolver

## Position

- Track: DNSSEC
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/dnssec/module-05/index.html`
- Source file: `src/protocol_in_code/dnssec/validator_loop.py`
- Walkthrough script: `examples/dnssec/session_05_walkthrough.py`

## Core Question

What does the smallest object look like that can be handed a name, a type, and a signed answer, and say — with a full trace — whether that answer is provably correct, provably wrong, or provably absent of proof?

## Outcome

By the end of this session, the learner should be able to:

- name every field on `ToyValidatingResolver` and which earlier session's module owns the logic behind it
- explain why `resolve_and_validate()` checks the answer's name and type *before* calling into `validate_chain()`
- read a `ValidationReport`'s `trace_slice` and say which zone and which key produced each line
- run the demo tree through all four `ChainOutcome` values using the same resolver and the same starting tree

## Read Order

1. Read the module comment above `ToyValidatingResolver` about what it trusts and what it computes
2. Read `ValidationReport` and `format_trace()`
3. Read `ToyValidatingResolver`'s field list
4. Read `resolve_and_validate()` top to bottom
5. Read `build_demo_tree()`
6. Read `tamper_record()`, `tamper_ds()`, `unsign_child()`
7. Run `examples/dnssec/session_05_walkthrough.py`

## Read It Like Code

```python
ToyValidatingResolver(
    zones,
    trust_anchor,
    clock,
    trace,
)
```

## Parts List

Every field and every function `validator_loop.py` imports was taught by an earlier session in this track. The capstone's only new code is the name/type guard in `resolve_and_validate()` and the demo-tree wiring below it.

| Import | Session that taught it | What it contributes to `ToyValidatingResolver` |
|---|---|---|
| `rrsig.Rrset`, `Rrsig`, `sign_rrset` | 01 | The signed-answer shape every scenario is built from; `verify_rrsig()` (called inside `validate_chain()`) is the first check on every hop. |
| `dnskey.DnsKey`, `KeyRole`, `make_key`, `sign_key_rrset` | 02 | The KSK/ZSK pair every zone in `build_demo_tree()` holds, and the signature that binds them into one DNSKEY rrset. |
| `ds.Ds`, `make_ds` | 03 | `trust_anchor`'s type, and the cross-zone fingerprint `ds_for_children` stores at every parent. |
| `chain.ChainOutcome`, `ChainResult`, `ZoneData`, `validate_chain` | 04 | `zones`'s element type, and the entire walk `resolve_and_validate()` delegates to after its own guard clause. |

## Decision Flow

```text
resolve_and_validate(name, rtype, rrset, rrsig):
  1. rrset.name != name   -> BOGUS_RECORD_SIG, trace: "answer name mismatch", stop
  2. rrset.rtype != rtype -> BOGUS_RECORD_SIG, trace: "answer type mismatch", stop
  3. otherwise            -> validate_chain(rrset, rrsig, zones, trust_anchor, clock)
                              result appended to self.trace, returned as ValidationReport
```

`validate_chain()` itself is Session 04's walk, unchanged: record RRSIG under the ZSK, DNSKEY rrset under the KSK, KSK hash against the parent's DS, repeated to the trust anchor.

## Reading Lens

The important move in this session is to stop reading `chain.py` and `validator_loop.py` as two separate things and start asking:

- what does this resolver actually trust on say-so, versus what does it prove by recomputing a hash or a signature?
- which line of `resolve_and_validate()` runs *before* `validate_chain()` is even called, and why does a name/type mismatch reuse `BOGUS_RECORD_SIG` rather than get its own outcome?
- what does advancing `self.clock` with `tick()` change about a trace that was SECURE a moment ago?

The capstone's thesis, stated directly in the module comment: the resolver trusts exactly **one** key it was *given* — `trust_anchor`, pinned out of band, never verified against anything else — and every other fact along the way — each ZSK, each KSK, each DS digest — it *computes* its way up to by recomputing a sha256 and comparing. Nothing else is trusted on say-so. Read every `ChainOutcome` other than the missing-key/missing-zone branches as evidence of that: SECURE means the arithmetic closed the loop all the way to `trust_anchor`; every BOGUS variant means one specific piece of arithmetic didn't match; INSECURE means there was no arithmetic to run.

## Toy Model Boundary

`ToyValidatingResolver` is handed the whole `zones` tree and the signed answer up front — it does not fetch DNSKEY, DS, or RRSIG records itself over the network. A real validating resolver (RFC 4035 §5) performs that fan-out hop by hop; the DNS track's `walk_from_root()` and referral machinery already model the transport side of that walk. Keeping the two apart is deliberate: this module is only about what happens once the records are in hand.

There is no authenticated denial of existence here (no NSEC/NSEC3) — see Session 04's Toy Model Boundary for why `unsign_child()`'s INSECURE result is trusted at face value rather than proven. There are no signature algorithms and no key rollover: a KSK or ZSK in this toy is a single unchanging secret string for the lifetime of the scenario. Expiration is real arithmetic (`now >= rrsig.expiration`), but there is no mechanism here for a resolver to notice a key is *about* to expire or to fetch a replacement — `tick()` only advances an integer.

## Code Landmarks

### The module comment above `ToyValidatingResolver`

States the capstone thesis directly: one key given, everything else computed. Read it before the class.

### `resolve_and_validate()`'s two guard clauses

```python
if rrset.name != name:
    ...
    return ValidationReport(ChainOutcome.BOGUS_RECORD_SIG, (self.trace[-1],))
if rrset.rtype != rtype:
    ...
    return ValidationReport(ChainOutcome.BOGUS_RECORD_SIG, (self.trace[-1],))
```

Both mismatches reuse `ChainOutcome.BOGUS_RECORD_SIG` rather than a dedicated value — an answer that does not even match the question asked is treated the same as an answer whose signature failed, because in both cases the resolver refuses to trust what it was handed. Neither guard calls into `validate_chain()` at all; the chain walk never sees a mismatched answer.

### `self.trace` versus a report's `trace_slice`

`self.trace` accumulates across every call the resolver makes over its lifetime; `ValidationReport.trace_slice` is only the lines from the *current* call. `format_trace()` renders a report's slice, not the resolver's whole history — the walkthrough's demo prints one call's story, not the resolver's full log.

### `build_demo_tree()`'s delegation wiring

```python
root_data.ds_for_children["com"] = make_ds(com_ksk)
com_data.ds_for_children["example.com"] = make_ds(example_ksk)
```

This is the entire tree's trust structure in two lines: root vouches for com's KSK, com vouches for example.com's KSK. `trust_anchor` itself is `make_ds(root_ksk)` — the same function, applied one more time, with nothing above it.

### The three knob functions

`tamper_record()` returns a bare `Rrset`, meant to be fed alongside the *original* `rrsig` — the signature still covers the old records, so it silently stops matching. `tamper_ds()` and `unsign_child()` both return a whole new `DemoTree` with `com`'s `ZoneData` swapped out, because both need to change what the parent zone publishes, not the leaf answer.

## Failure Questions

Use the source file to answer these:

1. `resolve_and_validate()` checks `rrset.name != name` and `rrset.rtype != rtype` before calling `validate_chain()`. What `ChainOutcome` do both of these guard clauses produce, and why does that choice mean the walkthrough cannot distinguish "wrong name" from "signature forged" just by reading the outcome value alone?
2. `ToyValidatingResolver.trace` and `ValidationReport.trace_slice` are two different lists holding overlapping content. If you call `resolve_and_validate()` three times on the same resolver, how many lines does `self.trace` hold afterward, compared to any single call's `trace_slice`?
3. `trust_anchor` is typed as a `Ds`, built by `make_ds(root_ksk)` in `build_demo_tree()`. What does `validate_chain()` compare it against at the root, and what function performs that comparison?
4. `tick()` only ever does `self.clock += seconds`. Trace what changes inside `validate_chain()`'s first check (`verify_rrsig()` on the record) if `tick()` is called with a value larger than `DEFAULT_EXPIRATION` before `resolve_and_validate()` runs.
5. `unsign_child()` deletes `com_data.ds_for_children["example.com"]` and returns a new `DemoTree`. Why does this function need to rebuild `ZoneData` for `com` instead of mutating `tree.zones["com"].ds_for_children` directly?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dnssec/session_05_walkthrough.py
```

The walkthrough builds one `ToyValidatingResolver` over `build_demo_tree()`'s zones and trust anchor, resolves `example.com` A and confirms SECURE with the verified 7-line trace ending on the trust-anchor match, checks that `format_trace()` carries the per-level lines a doc author would paste under a demo, then runs each knob — `tamper_record`, `tamper_ds`, `unsign_child` — through a fresh resolver built over the knob's tampered tree and confirms each lands on its `ChainOutcome`. It finishes by advancing a resolver's clock past `DEFAULT_EXPIRATION` with `tick()` and confirming the record signature is caught as expired at the very first hop, and by asking for an answer under the wrong name and confirming the guard clause fires before any chain walk begins.

## Done When

The learner can say all of the following without looking at notes:

- "The resolver trusts one Ds it was given — trust_anchor — and arithmetics its way to everything else."
- "resolve_and_validate() checks the answer matches the question before it ever calls validate_chain(); a mismatch never reaches the chain walk."
- "A SECURE trace is always the same shape for the same tree depth: one record-sig line, then a key-sig/DS-match pair per zone, ending on the trust-anchor match."
- "Advancing the clock past a signature's expiration turns SECURE into BOGUS_RECORD_SIG at the very first hop — the record's own zone catches it before the walk ever reaches the parent."
- "Everything in this file was built in Sessions 01 through 04; validator_loop.py only wires build_demo_tree, the three knobs, and the name/type guard around validate_chain()."

## Bolt-On Point

`ToyValidatingResolver` is handed a finished `(rrset, rrsig)` pair — it never fetches one. The DNS track's `ToyResolver` (`src/protocol_in_code/dns/resolver.py`, DNS Session 08) is the component that actually walks the tree over a transport and produces records; bolting the two together means DNS Session 08's resolver would fetch the RRSIG alongside the record it already fetches, then hand both to `resolve_and_validate()` before trusting the answer. Neither file currently does this wiring — it is the natural next exercise once both capstones are read, not something either capstone builds for you.

## References

- RFC 4033 (DNS Security Introduction and Requirements — the "resolver trusts one key" framing this session's thesis is built on)
- RFC 4035 Section 5 (Authenticating DNS Responses — the validation algorithm this module's `resolve_and_validate()` is a toy version of)
