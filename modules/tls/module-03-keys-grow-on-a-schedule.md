# Session 03 / Module 03: Keys Grow on a Schedule

## Position

- Track: TLS
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/tls/module-03/index.html`
- Source file: `src/protocol_in_code/tls/key_schedule.py`
- Walkthrough script: `examples/tls/session_03_walkthrough.py`

## Core Question

Where does each TLS secret actually come from, and why can none of them be computed out of order?

## Outcome

By the end of this session, the learner should be able to:

- explain `derive()` as a stand-in for HKDF-Expand-Label, and state exactly what it is not
- walk the chain early_secret -> handshake_secret -> master_secret and say what new input (if any) is mixed in at each stage
- explain why `client_hs_traffic` and `server_hs_traffic` are two different values derived from the same `handshake_secret`
- explain why `advance_to_master()` raises if called before `advance_to_handshake()`

## Read Order

1. Read the module-level comment at the top of the file
2. Read `derive()`
3. Read `KeySchedule`
4. Read `start_schedule()`
5. Read `advance_to_handshake()`
6. Read `advance_to_master()`
7. Run `examples/tls/session_03_walkthrough.py`

## Read It Like Code

```python
KeySchedule(
    early_secret,
    handshake_secret=None,
    master_secret=None,
    client_hs_traffic=None,
    server_hs_traffic=None,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `early_secret` | Seeded once, from the PSK, at construction time. Never `None`. |
| `handshake_secret` | `None` until `advance_to_handshake()` runs. Mixes the (EC)DHE shared key into `early_secret`. |
| `master_secret` | `None` until `advance_to_master()` runs. Derived from `handshake_secret` alone - no new external input. |
| `client_hs_traffic` | Derived from `handshake_secret` with the label `"client hs traffic"`. Set alongside `handshake_secret`. |
| `server_hs_traffic` | Derived from `handshake_secret` with the label `"server hs traffic"`. Same secret, different label, different value. |

## Decision Flow

```text
start_schedule(psk)                                  -> early_secret = derive(psk, "early secret")
advance_to_handshake(schedule, shared_key)            -> handshake_secret = derive(early_secret, "handshake secret", shared_key)
                                                          client_hs_traffic = derive(handshake_secret, "client hs traffic")
                                                          server_hs_traffic = derive(handshake_secret, "server hs traffic")
advance_to_master(schedule)                            -> if handshake_secret is None: raise ValueError
                                                          master_secret = derive(handshake_secret, "master secret")
```

## Reading Lens

The important move in this session is to stop thinking of "the key" as one value and start asking:

- which secret is this one derived FROM?
- what label distinguishes it from every other secret derived from the same input?
- is there new external material mixed in at this stage, or is it derived from internal state alone?

## Toy Model Boundary

`derive()` is a single sha256 hexdigest over the concatenation of `secret`, `label`, and `context`. The module comment says plainly that this is a toy stand-in for HKDF-Extract / HKDF-Expand-Label (RFC 8446 SS7.1) and makes no cryptographic strength claim. Do not read anything here as real key derivation: there is no HMAC, no expand-with-length-prefix, no separation between Extract and Expand, and no key material of a fixed cryptographic size - just a hex string standing in for one.

There is also no actual (EC)DHE math anywhere in this module. `shared_key` in `advance_to_handshake()` is just a string the caller supplies; nothing here performs a Diffie-Hellman computation to produce it. The lesson is the *shape* of the schedule - what depends on what, and in what order - not the cryptography that fills each step in a real implementation.

## Code Landmarks

### `derive()`

One line of real logic: `hashlib.sha256(f"{secret}|{label}|{context}".encode()).hexdigest()`. Same three inputs always produce the same output - this is what makes every stage of the schedule reproducible and testable.

### `KeySchedule`

A mutable dataclass, unlike `ClientHello`/`ServerHello` in Session 01. The schedule is built up in place across three function calls, so it cannot be frozen - each `advance_*` function mutates fields on the instance it is given.

### `start_schedule()`

The only place `early_secret` is ever set. It calls `derive()` once, with the label `"early secret"` and no context. An empty-string PSK is legal - the default `psk=""` produces a real digest.

### `advance_to_handshake()`

Three `derive()` calls in a row, all keyed off `handshake_secret` for the last two. Note `client_hs_traffic` and `server_hs_traffic` are computed from the *same* `handshake_secret` - only the label string differs, and that alone is enough to make them different digests.

### `advance_to_master()`

Guarded by an explicit `if schedule.handshake_secret is None: raise ValueError`. This is the one place in the file that enforces order - you cannot skip a stage.

## Failure Questions

Use the source file to answer these:

1. `advance_to_handshake()` sets three fields on the schedule. Which of the three uses `shared_key` directly as an argument to `derive()`, and which two do not?
2. If you call `start_schedule(psk="a")` twice, do the two `early_secret` values match? What single property of `derive()` guarantees your answer?
3. `advance_to_master()` calls `derive(schedule.handshake_secret, "master secret")` with no third argument. What does `context` default to inside `derive()` when it is omitted this way?
4. Construct a fresh `KeySchedule` by calling only `start_schedule()`. What exception, if any, do you get from calling `advance_to_master()` on it directly, and which line raises it?
5. `client_hs_traffic` and `server_hs_traffic` are both derived from `handshake_secret`. Given that `derive()` is a pure function of its three arguments, what is the only thing that can make these two outputs differ?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tls/session_03_walkthrough.py
```

The walkthrough shows `derive()` is deterministic and label-sensitive, runs the same psk/shared_key pair through two independent schedules to confirm identical master secrets, then changes only the psk to show every downstream secret changes, confirms `client_hs_traffic != server_hs_traffic`, and finally calls `advance_to_master()` on a schedule with no handshake secret to show the guard raising.

## Done When

The learner can say all of the following without looking at notes:

- "`derive()` is sha256 over (secret, label, context) - an honest stand-in for HKDF-Expand-Label, not real cryptography."
- "Every secret in the schedule is derived from the one before it, plus a label, plus sometimes new external material - never from scratch."
- "Changing the psk changes early_secret, which changes handshake_secret, which changes master_secret and both traffic secrets - the chain propagates all the way down."

## References

- RFC 8446 Section 7.1 (Key Schedule)
