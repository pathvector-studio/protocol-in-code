# Session 08 / Module 08: Failure Is a Typed Message

## Position

- Track: TLS
- Session: 08
- Site lesson: `pathvector-site/courses/protocols-in-code/tls/module-08/index.html`
- Source file: `src/protocol_in_code/tls/alert.py`
- Walkthrough script: `examples/tls/session_08_walkthrough.py`

## Core Question

When something goes wrong in a handshake, what exactly gets sent back, who decides what it means, and does the connection actually end?

## Outcome

By the end of this session, the learner should be able to:

- name the two fields on `Alert` and explain why a failure is a value, not an exception
- state the rule `classify()` uses to decide `CLOSE_CONNECTION` versus `IGNORE_AND_CONTINUE`, including the one non-FATAL case that still closes
- read the `alert_for_chain_verdict()` table and name the alert for every non-TRUSTED verdict
- explain why `alert_for_*` functions return `Alert | None` instead of always returning an alert

## Read Order

1. Read `AlertLevel`, `AlertDescription`, `AlertAction`
2. Read `Alert`
3. Read `classify()`
4. Read `alert_for_negotiation_outcome()`
5. Read `alert_for_chain_verdict()` — the mapping table
6. Read `alert_for_hostname_verdict()`
7. Read `alert_for_unprotect_outcome()`
8. Run `examples/tls/session_08_walkthrough.py`

## Read It Like Code

```python
Alert(
    level,
    description,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `level` | `WARNING` or `FATAL`. Drives most of `classify()`'s decision by itself. |
| `description` | The specific reason. One value, `CLOSE_NOTIFY`, changes the classification even at `WARNING` level. |

## Decision Flow

```text
classify(alert):
  alert.level is FATAL                        -> CLOSE_CONNECTION
  alert.level is WARNING, description is
    CLOSE_NOTIFY                               -> CLOSE_CONNECTION
  alert.level is WARNING, anything else        -> IGNORE_AND_CONTINUE
```

## Reading Lens

The important move in this session is to stop treating "alert" as a synonym for "error" and start asking:

- is this alert actually FATAL, or does it only look serious?
- does this alert's `description` change how it is classified, independent of its `level`?
- for each `alert_for_*` function, what input value maps to `None` — and what does `None` mean for the caller?

## Toy Model Boundary

This module models neither alert encryption nor alert ordering. Real TLS 1.3 sends alerts as protected records once keys are established (RFC 8446 SS6), and a peer that sends a FATAL alert is expected to close the underlying transport immediately afterward. Here `Alert` is a plain value and `classify()` returns an intent (`CLOSE_CONNECTION` or `IGNORE_AND_CONTINUE`) with no wire encoding, no encryption, and no notion of "before" or "after" other messages. The `alert_for_*` mapping functions are pure — given a verdict from chain, hostname, negotiation, or record-layer code, they return the alert or `None`, with no side effects and no network call implied.

## Code Landmarks

### `classify()`

The reading target's first stop. Its docstring states the rule directly: "CLOSE_NOTIFY is the orderly goodbye; every other FATAL alert closes just the same." Note the order of the two `if` statements — FATAL is checked before CLOSE_NOTIFY, so a hypothetical FATAL CLOSE_NOTIFY (never constructed elsewhere in this codebase) would still resolve to `CLOSE_CONNECTION` through the first branch.

### `alert_for_chain_verdict()`'s mapping table

A literal `dict` from every `ChainVerdict` member to an `Alert` or `None` — this is the reading target of the whole module. Two verdicts, `EMPTY_CHAIN` and `BROKEN_CHAIN`, share `CERTIFICATE_UNKNOWN`. Two others, `EXPIRED` and `NOT_YET_VALID`, share `CERTIFICATE_EXPIRED`. Only `UNTRUSTED_ROOT` maps to `UNKNOWN_CA`.

### `alert_for_unprotect_outcome()`

Mirrors Session 07's collapse: every non-`OK` `UnprotectOutcome` — meaning `BAD_TAG` is the only one `unprotect()` ever actually produces — maps to the same `BAD_RECORD_MAC` alert. The typed-failure story continues one layer up: record layer collapses tamper/wrong-key/wrong-seq into `BAD_TAG`; alert layer reports all of that as one `BAD_RECORD_MAC`.

## Failure Questions

Use the source file to answer these:

1. Construct an `Alert` with `level=WARNING` and `description=CLOSE_NOTIFY`. Does `classify()` return `CLOSE_CONNECTION` or `IGNORE_AND_CONTINUE`? Which `if` branch decides it?
2. `alert_for_chain_verdict()` maps both `EMPTY_CHAIN` and `BROKEN_CHAIN` to `CERTIFICATE_UNKNOWN`. Name the one `ChainVerdict` member that maps to `None` instead.
3. `alert_for_negotiation_outcome()` takes a `NegotiationOutcome`, which has three members (`CHOSEN`, `NO_OVERLAP`, `NO_VERSION_OVERLAP`). How many of those three produce a `HANDSHAKE_FAILURE` alert, and how does the function's code decide that without naming both non-CHOSEN members explicitly?
4. `alert_for_hostname_verdict()` is given a `HostnameVerdict` with three members. How many distinct alerts can this function actually return, and what does that imply about `MATCHED_EXACT` versus `MATCHED_WILDCARD`?
5. `AlertDescription` declares seven members. Which two are never returned by any `alert_for_*` function in this file?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tls/session_08_walkthrough.py
```

The walkthrough classifies a `WARNING` `CLOSE_NOTIFY`, a `FATAL` alert, and an ordinary `WARNING`, then walks the chain-verdict table for `EXPIRED`, `UNTRUSTED_ROOT`, and `TRUSTED`, and finishes with the hostname `NO_MATCH` and record-layer `BAD_TAG` mappings.

## Done When

The learner can say all of the following without looking at notes:

- "An alert is a value with a level and a description — nothing about it is free-form text."
- "classify() closes the connection for every FATAL alert, plus the one WARNING case that means goodbye: CLOSE_NOTIFY."
- "Every alert_for_* function is a pure mapping from an earlier session's verdict to an Alert or None — read the table, don't guess it."

## References

- RFC 8446 Section 6 (Alert Protocol)
