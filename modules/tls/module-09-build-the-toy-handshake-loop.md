# Session 09 / Module 09: Build the Toy Handshake Loop

## Position

- Track: TLS
- Session: 09 (track capstone)
- Site lesson: `pathvector-site/courses/protocols-in-code/tls/module-09/index.html`
- Source file: `src/protocol_in_code/tls/handshake_loop.py`
- Walkthrough script: `examples/tls/session_09_walkthrough.py`

## Core Question

What does a complete TLS 1.3 handshake look like when hello, negotiation, chain verification, hostname matching, key schedule, ticket issuance, and one protected record are all wired into two functions instead of eight separate demos?

## Outcome

By the end of this session, the learner should be able to:

- name every module this file imports and which earlier session taught it
- trace `run_handshake()` top to bottom and say, at each step, which earlier session's function just ran
- explain why a ticket HIT in `run_resumed_handshake()` never calls `verify_chain()` or `match_hostname()`, and how the trace proves the skip
- explain why `run_resumed_handshake()` falls back to `run_handshake()` on anything other than a ticket HIT
- read a `HandshakeOutcome` and say whether the failure happened at negotiation, chain verification, hostname matching, or the record layer

## Read Order

1. Read the module comment and `SHARED_KEY` / `TICKET_LIFETIME`
2. Read `ToyTlsConfig`, `ToyTlsClient`, `ToyTlsServer`, `HandshakeOutcome`
3. Read `_fail()`
4. Read `run_handshake()` top to bottom, mapping each block back to its session (see Parts List)
5. Read `run_resumed_handshake()`, comparing it step for step against `run_handshake()`
6. Run `examples/tls/session_09_walkthrough.py`
7. Read the printed traces and label each line with its session

## Read It Like Code

```python
ToyTlsConfig(
    versions,
    cipher_suites,
    chain,
    trust_store,
)

ToyTlsClient(name, config, trace)
ToyTlsServer(name, config, tickets, trace)

HandshakeOutcome(
    completed,
    alert,
    trace,
    ticket_name,
)
```

## Parts List

Every function `handshake_loop.py` imports was taught by an earlier session in this track. The capstone's only new code is the wiring between them, plus `SHARED_KEY` and `TICKET_LIFETIME`.

| Import | Session that taught it | What it contributes to `run_handshake()` / `run_resumed_handshake()` |
|---|---|---|
| `messages.ClientHello`, `ServerHello` | 01 | The hello and its reply, built and sent as plain values. `validate_client_hello()` from Session 01 is **not** called here — the loop builds a well-formed hello directly and never exercises `HelloValidity`. |
| `negotiate.NegotiationOutcome`, `choose_suite`, `choose_version` | 02 | Version and cipher-suite agreement, first two negotiation steps in `run_handshake()`. |
| `key_schedule.KeySchedule`, `start_schedule`, `advance_to_handshake`, `advance_to_master` | 03 | `client_schedule` / `server_schedule` (and `resumed_schedule`); walked from early secret to master secret on both full and resumed paths. |
| `chain.Certificate`, `ChainVerdict`, `verify_chain` | 04 | Chain verification against `trust_store`, run once per full handshake — and structurally skipped on a ticket HIT. |
| `hostname.HostnameVerdict`, `match_hostname` | 05 | Hostname matching against the leaf certificate's subject — likewise skipped on a ticket HIT. |
| `resumption.TicketOutcome`, `TicketStore`, `issue_ticket`, `lookup_ticket` | 06 | `server.tickets`; every full handshake issues a ticket, every resumption attempt looks one up first. |
| `record.UnprotectOutcome`, `protect`, `unprotect` | 07 | One application-data record sealed by the client and opened by the server on both the full and resumed paths, keyed by the schedule's `master_secret`. |
| `alert.Alert`, `alert_for_negotiation_outcome`, `alert_for_chain_verdict`, `alert_for_hostname_verdict`, `alert_for_unprotect_outcome` | 08 | Every failure exit in `_fail()` carries a typed `Alert` produced by one of these four mapping functions. |

## Decision Flow

```text
run_handshake(client, server, trust_store, now):
  1. build ClientHello from client.config, send it              (01)
  2. choose_version(...)          not CHOSEN -> fail: HANDSHAKE_FAILURE   (02, 08)
  3. choose_suite(...)            not CHOSEN -> fail: HANDSHAKE_FAILURE   (02, 08)
  4. build ServerHello, send it                                   (01)
  5. verify_chain(...)            not TRUSTED -> fail: per chain table   (04, 08)
  6. match_hostname(...)          NO_MATCH    -> fail: UNRECOGNIZED_NAME (05, 08)
  7. advance both schedules: early -> handshake -> master          (03)
  8. issue_ticket(...) on the server                               (06)
  9. protect() one record, unprotect() it on the server            (07)
     not OK -> fail: BAD_RECORD_MAC                                (08)
  10. completed=True, ticket_name set

run_resumed_handshake(client, server, ticket_name, now):
  1. lookup_ticket(...)                                            (06)
     not HIT -> fall back to run_handshake() in full, unconditionally
     HIT     -> trace "chain verification SKIPPED", skip steps 5-6 above entirely
  2. start_schedule(psk=ticket.master_secret), advance to master   (03)
  3. protect() / unprotect() one record, same as full path         (07)
     not OK -> fail: BAD_RECORD_MAC                                (08)
  4. completed=True, ticket_name unchanged
```

## Reading Lens

The important move in this session is to stop reading `run_handshake()` as one long function and start asking, at every call:

- which of the eight imported modules is doing the actual work on this line, and which session taught it?
- if this line's result is a failure verdict, which `alert_for_*` function turns it into an `Alert`, and what does `classify()` (Session 08) say happens next?
- on the resumed path, which two calls from the full path are structurally absent — not skipped by an `if`, but never written at all?

## Toy Model Boundary

This module does not perform a real key exchange. `SHARED_KEY` is a single constant string standing in for what a real handshake would derive from (EC)DHE — every handshake in this codebase, full or resumed, mixes in the exact same "shared secret," so nothing here demonstrates forward secrecy or per-connection key uniqueness. The handshake is a single round trip: one `ClientHello`, one `ServerHello`, no `HelloRetryRequest` and no second flight. There is no 0-RTT: `run_resumed_handshake()` still performs a full round trip and derives keys before either side sends application data, unlike real TLS 1.3 early data. `chain[0]` is treated as the SAN list in `run_handshake()` (`san_names = (leaf.subject,)`) — there is no separate Subject Alternative Name field on `Certificate`, so hostname matching runs against the same string used to build the `ClientHello`'s `server_name`. And as in Sessions 07 and 08, every failure path collapses several possible real causes into one typed `Alert`; the capstone does not change that behavior, only chains it end to end.

## Code Landmarks

### The module comment above `SHARED_KEY`

Two constants, one line each, both worth reading before the functions: `SHARED_KEY` names the toy substitution explicitly; `TICKET_LIFETIME = 3600` is the only place this file decides how long a ticket is good for.

### `_fail()`

Every failure exit in this file — five of them across both functions — routes through this one helper. It appends the same trace line to both `client.trace` and `server.trace`, then returns a `HandshakeOutcome` with `completed=False`. Read this once; every early return below it does the same thing.

### `run_handshake()`'s ordering

Version and suite negotiation happen before chain verification, which happens before hostname matching, which happens before the key schedule advances. Every check that can fail runs before any cryptographic material is derived — nothing is wasted deriving keys for a handshake that was always going to abort.

### `run_resumed_handshake()`'s early return

`if lookup.outcome is not TicketOutcome.HIT: ... return run_handshake(...)`. A resumption attempt that doesn't find a valid ticket is not a distinct failure mode — it silently becomes an ordinary full handshake. The trace shows the fallback line, but the `HandshakeOutcome` it returns is indistinguishable in shape from a first-time full handshake.

### The two trace lines that only exist on the resumed path

`"chain verification SKIPPED: resuming from ticket's master secret"` is appended to *both* `client.trace` and `server.trace` immediately after a ticket HIT, in the exact spot where `verify_chain()` and `match_hostname()` would have run on the full path. There is no corresponding line — SKIPPED or otherwise — on the full-handshake path, because there is nothing to skip there.

## Failure Questions

Use the source file to answer these:

1. `run_handshake()` computes `hostname` from `client.config.chain[0].subject if client.config.chain else "example.com"` before sending the `ClientHello`. What hostname does a client with an empty `chain` tuple offer, and what would `match_hostname()` be checking against on the server side in that case?
2. `_fail()` builds its trace line from `alert.level.value` and `alert.description.value`. Trace a no-suite-overlap handshake: which `alert_for_*` function is called, and what two-word phrase appears in the resulting trace line?
3. `run_resumed_handshake()` calls `start_schedule(psk=lookup.ticket.master_secret)` instead of `start_schedule()` with no argument. Compare this to `run_handshake()`'s `start_schedule()` call — what does the `psk` parameter change about the resulting `early_secret`, per `key_schedule.py`?
4. Both `run_handshake()` and `run_resumed_handshake()` call `protect("application data", ..., seq=0)`. If a real connection reused `run_handshake()`'s `application_key` for a second record without incrementing `seq`, what would Session 07's `unprotect()` do — and is that scenario exercised anywhere in this file?
5. `ToyTlsServer.tickets` is a fresh `TicketStore()` by default via `field(default_factory=TicketStore)`. If two separate `ToyTlsServer` instances are used — one for the full handshake, a different one for the resumption attempt — what outcome does `lookup_ticket()` return, and which branch of `run_resumed_handshake()` runs as a result?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tls/session_09_walkthrough.py
```

The walkthrough runs a full handshake to completion and checks both traces are populated, runs a no-suite-overlap configuration to `HANDSHAKE_FAILURE`, runs an expired-certificate server to `CERTIFICATE_EXPIRED`, then resumes the first handshake's session using its issued ticket — checking the resumed handshake completes, that its trace contains a `SKIPPED` line, and that the resumed portion of the trace contains no `"verifies chain"` entry at all.

## Done When

The learner can say all of the following without looking at notes:

- "Every field and every function in this file belongs to an earlier session; this module only wires them together in two functions."
- "run_handshake() checks negotiation, then chain, then hostname, then derives keys — every possible abort happens before any key material exists."
- "A ticket HIT doesn't skip chain and hostname verification with an if — it takes a different code path that never calls those functions at all, and the trace says so."

## References

- RFC 8446 Section 2 (Protocol Overview — the full handshake this loop compresses)
- RFC 8446 Section 4.2.11 / Section 2.2 (Pre-Shared Key / resumption, cross-referenced from Session 06)
- RFC 8446 Section 4.1 (Key Exchange Messages, cross-referenced from Sessions 01-02)
- RFC 8446 Section 4.4.2 (Certificate, cross-referenced from Session 04)
- RFC 8446 Section 7.1 (Key Schedule, cross-referenced from Session 03)
- RFC 8446 Section 5.1 / 5.2 (Record Layer, cross-referenced from Session 07)
- RFC 8446 Section 6 (Alert Protocol, cross-referenced from Session 08)
