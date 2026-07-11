# Session 07 / Module 07: Failure Has Flavors

## Position

- Track: DNS
- Session: 07
- Site lesson: `pathvector-site/courses/protocols-in-code/dns/module-07/index.html`
- Source file: `src/protocol_in_code/dns/failures.py`
- Walkthrough script: `examples/dns/session_07_walkthrough.py`

## Core Question

NXDOMAIN, SERVFAIL, and a timeout all mean "no IP address". Why does a resolver treat one as an answer and the others as reasons to try again?

## Outcome

By the end of this session, the learner should be able to:

- classify one server attempt into Answered, NXDOMAIN, SERVFAIL, REFUSED, or Timeout
- explain why NXDOMAIN stops the fallback while SERVFAIL does not
- describe server fallback as an ordered loop with an early exit
- explain what the resolver reports when every server fails differently

## Read Order

1. Read `ServerAttempt`
2. Read `classify_attempt()`
3. Read `is_final()`
4. Read `try_servers()`
5. Run `examples/dns/session_07_walkthrough.py`
6. For each scenario, predict `answered_by` and `tried` before looking

## Read It Like Code

```python
ServerAttempt(
    server,
    timed_out,
    rcode,
    records,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `timed_out` | Silence is not an rcode. It has to be modeled as its own field, checked first. |
| `rcode` | The server's verdict when it did respond. |
| `records` | Only meaningful when the attempt is classified as Answered. |
| `server` | Identity matters: the result reports who answered and who was tried. |

## Decision Flow

```text
classify one attempt:
  timed_out          -> Timeout
  rcode NXDOMAIN     -> NameError
  rcode SERVFAIL     -> ServerFailure
  rcode REFUSED      -> Refused
  otherwise          -> Answered

is it final?
  Answered, NameError   -> yes, stop the fallback
  everything else       -> no, try the next server
```

## Reading Lens

The important move in this session is to stop reading every failed lookup as "DNS is down" and start asking:

- is this verdict about the name or about the server?
- which attempt in the list produced the final outcome?
- how many servers were tried before the loop stopped?

## Toy Model Boundary

Real resolvers add retry timers, exponential backoff, and per-server reputation. This lesson keeps the attempts as a pre-built tuple so the only logic under study is classification and the stop/continue decision.

The `attempts` tuple plays the role of "what each server would say if asked" — the loop decides how far down the list the resolver actually gets.

## Code Landmarks

### `classify_attempt()`

Timeout is checked before rcode, because a timed-out attempt has no rcode worth reading.

### `is_final()`

The single most important line in the file. NXDOMAIN is grouped with Answered, not with the failures — an authoritative "this name does not exist" is information about the name, and asking another server cannot change it.

### `try_servers()`

An ordered loop with an early exit. Note what happens when nothing is final: the result carries the last non-final kind and an empty `answered_by`.

## Failure Questions

Use the source file to answer these:

1. Why does the NXDOMAIN scenario stop after one attempt even though the second server has records?
2. Which classification comes back for an attempt with both `timed_out=True` and `rcode="SERVFAIL"`, and why?
3. When every server fails, which kind does the result carry?
4. Why is REFUSED retryable here while NXDOMAIN is not?
5. What does an empty `answered_by` tell you that the kind alone does not?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dns/session_07_walkthrough.py
```

The walkthrough runs five server lists and prints who answered and how many servers were tried.

## Done When

The learner can say all of the following without looking at notes:

- "NXDOMAIN is an answer about the name. SERVFAIL and timeout are complaints about a server."
- "Fallback is an ordered loop that stops on the first final outcome."
- "Retrying a different server can fix a server problem, never a name problem."

## References

- RFC 1035 Section 4.1.1 (RCODE)
- RFC 2308 Section 2.1 (name errors)
- RFC 4697 (observed resolver misbehavior, including retry storms)
