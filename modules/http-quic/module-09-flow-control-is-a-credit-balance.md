# Session 09 / Module 09: Flow Control Is a Credit Balance

## Position

- Track: HTTP/QUIC
- Session: 09
- Site lesson: `pathvector-site/courses/protocols-in-code/http-quic/module-09/index.html`
- Source file: `src/protocol_in_code/quic/flow_control.py`
- Walkthrough script: `examples/http-quic/session_09_walkthrough.py`

## Core Question

QUIC enforces flow control at two levels at once — per stream and per connection. What decides whether a send goes through, and what exactly happens to each level's balance when the answer is no?

## Outcome

By the end of this session, the learner should be able to:

- state the one field pair (`limit`, `consumed`) that backs both stream-level and connection-level accounting
- trace `send_on_stream()`'s check order and say which level is tested first
- explain why a blocked send leaves both accounts completely unchanged
- explain why `grant()` can silently do nothing

## Read Order

1. Read the module comment above `SendDecision` (the RFC 9000 §4 reference)
2. Read `CreditAccount`
3. Read `can_send()`
4. Read `consume()`
5. Read `grant()`
6. Read `send_on_stream()`
7. Run `examples/http-quic/session_09_walkthrough.py`

## Read It Like Code

```python
CreditAccount(
    limit,      # the most this account may ever have consumed
    consumed,   # how much has actually been sent against it so far
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `limit` | The receiver-granted ceiling. Only `grant()` can move it, and only upward. |
| `consumed` | Running total of bytes sent against this account. Only `consume()` increments it, and only after both checks in `send_on_stream()` pass. |

## Decision Flow

```text
send_on_stream(conn_account, stream_account, n):
  1. can_send(stream_account, n) is False  -> BLOCKED_BY_STREAM      (nothing consumed anywhere)
  2. can_send(conn_account, n) is False    -> BLOCKED_BY_CONNECTION  (nothing consumed anywhere)
  3. otherwise                             -> consume(stream_account, n)
                                               consume(conn_account, n)
                                               SENT
```

## Reading Lens

The important move in this session is to stop thinking of "stream limit" and "connection limit" as two different mechanisms and start seeing them as the same `CreditAccount` shape, checked twice in a fixed order. Read every `send_on_stream()` call asking:

- which account does `can_send()` reject first — is it ever possible to reach the connection-level check before the stream-level one has passed?
- on a blocked send, did `consume()` run on either account? How would you prove that from the source alone, not just from behavior?
- after a `grant()` call, is the new `limit` always the value passed in, or only sometimes?

## Toy Model Boundary

Real QUIC flow control is bidirectional and signaled on the wire: a receiver sends `MAX_DATA` and `MAX_STREAM_DATA` frames to grant credit, and a blocked sender emits `DATA_BLOCKED` / `STREAM_DATA_BLOCKED` frames to say so. None of that framing exists here — `grant()` is called directly as a plain function, and a blocked `send_on_stream()` call simply returns an enum member with no signal sent anywhere. There is also no `MAX_STREAMS` accounting (the limit on how many streams may be open at all) — this module only tracks bytes on streams and the connection that already exist.

## Code Landmarks

### The module comment above `SendDecision`

Names RFC 9000 Section 4 directly and states the whole model in one sentence: a receiver grants a limit, a sender consumes against it, and the limit only ever moves up. Read this before anything else in the file.

### `CreditAccount`'s docstring

"One shape, two levels: the same credit balance backs both a stream and the connection." There is no separate `StreamCreditAccount` or `ConnectionCreditAccount` type — `send_on_stream()` is simply called with two different `CreditAccount` instances.

### `send_on_stream()`

```python
if not can_send(stream_account, n):
    return SendDecision.BLOCKED_BY_STREAM

if not can_send(conn_account, n):
    return SendDecision.BLOCKED_BY_CONNECTION

consume(stream_account, n)
consume(conn_account, n)
return SendDecision.SENT
```

The stream check runs first. `consume()` is called only after *both* checks pass — there is no code path where one account is consumed and the other is not.

### `grant()`

```python
if new_limit > account.limit:
    account.limit = new_limit
```

A single comparison. Calling `grant()` with a value at or below the current `limit` is a legal, silent no-op — nothing raises, nothing is logged, `limit` simply stays put.

## Failure Questions

Use the source file to answer these:

1. `send_on_stream()` calls `can_send()` on `stream_account` before `conn_account`. If a send would be blocked by *both* accounts, which `SendDecision` value is returned — does the caller ever learn about the connection-level shortfall?
2. A call to `send_on_stream()` returns `BLOCKED_BY_STREAM`. What is `conn_account.consumed` immediately afterward, compared to immediately before the call? Which lines in `send_on_stream()` guarantee this?
3. `grant(account, new_limit)` is called with a `new_limit` equal to `account.limit` exactly (not lower, not higher). Does `account.limit` change? Which comparison operator in `grant()` decides this edge case?
4. `can_send()` checks `account.consumed + n <= account.limit`. If `n` is 0, can `can_send()` ever return `False`, regardless of how exhausted the account is?
5. After a `BLOCKED_BY_CONNECTION` result, could a caller retry the exact same `send_on_stream()` call with the exact same arguments and get `SENT` without any intervening `grant()` call? What would have to be true about `stream_account` and `conn_account` for that to happen?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/http-quic/session_09_walkthrough.py
```

The walkthrough sends within both limits and checks both balances rise together, then exhausts stream-level credit and confirms both accounts are completely unchanged by the blocked send, then shows ample stream credit blocked by a tight connection account, then grants a higher connection limit and watches the same send go through, then shows a lower grant is silently ignored.

## Done When

The learner can say all of the following without looking at notes:

- "CreditAccount is one shape reused at both the stream and connection level — send_on_stream() is what makes it two-level."
- "A blocked send, whether by stream or connection, consumes nothing on either account — consume() only runs after both checks pass."
- "grant() only ever raises a limit; a lower value is a silent no-op, not an error."

## References

- RFC 9000 Section 4 (Flow Control)
