# Session 03 / Module 03: Three States, Both Directions

## Position

- Track: HA (VRRP+BFD)
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/ha/module-03/index.html`
- Source file: `src/protocol_in_code/ha/bfd.py`
- Walkthrough script: `examples/ha/session_03_walkthrough.py`

## Core Question

BFD has to agree on "the session is up" between two independent sides — how does a three-state machine reach agreement without a central decision-maker?

## Outcome

By the end of this session, the learner should be able to:

- name the three `BfdState` values and which one the state machine can never assign as a first move
- walk the DOWN -> INIT -> UP progression step by step, quoting which combination of local/remote state produces which transition
- explain why loss of the peer drops straight to DOWN with no INIT stopover
- state `detection_time` as a formula and compute it for a given multiplier and interval

## Read Order

1. Read the module docstring at the top of the file
2. Read `BfdState`
3. Read `BfdSession`
4. Read `on_packet()`
5. Read `detection_time()`
6. Read `check_timeout()`
7. Run `examples/ha/session_03_walkthrough.py`

## Read It Like Code

```python
BfdSession(
    local_state,
    remote_state_last_heard,
    detect_multiplier,
    interval_ms,
    last_packet_at,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `local_state` | What this side currently believes about the session. The value every caller reads. |
| `remote_state_last_heard` | What the peer last reported about *its* state. `on_packet()`'s whole decision rests on the pair `(local_state, remote_state_last_heard)`. |
| `detect_multiplier` | How many missed intervals count as a failure. Multiplies with `interval_ms` in `detection_time()`. |
| `interval_ms` | The expected spacing between control packets, in milliseconds — the scale this session runs at. |
| `last_packet_at` | The silence clock. `check_timeout()` measures from here, the same shape as `vrrp_timeout.py`'s `last_heard_at`. |

## Decision Flow

```text
on_packet(session, remote_state, now):
  always: remote_state_last_heard = remote_state; last_packet_at = now
  local DOWN + remote DOWN  -> local becomes INIT
  local DOWN + remote INIT  -> local becomes UP
  local INIT + remote INIT  -> local becomes UP
  local INIT + remote UP    -> local becomes UP
  anything else             -> local_state unchanged

check_timeout(session, now):
  now >= last_packet_at + detection_time(session)  -> local becomes DOWN
  otherwise                                          -> local_state unchanged
```

## Reading Lens

The important move in this session is to stop asking "what state is the session in?" and start asking, at every `on_packet()` call:

- what did *I* believe before this packet arrived?
- what does the packet say the *peer* believes?
- does that pair of beliefs appear in the table, and if not, why does the session hold its ground instead of guessing?

BFD is `vrrp_timeout.py`'s silence-means-failure again, but the questions are different. VRRP infers failure in one direction only — the backup listens for the master, never the reverse. BFD negotiates in both directions at once: each side's `local_state` climbs only as far as what it has heard the other side currently claims, and the local state is one field, not a shared one — the two sides can genuinely disagree for a call or two before they converge.

## Toy Model Boundary

Real BFD supports echo mode (looping packets off the peer's forwarding plane without involving its control plane) and optional authentication on control packets — neither exists here. This module also collapses the RFC's `AdminDown` state into nothing; `BfdState` only has `DOWN`, `INIT`, and `UP`. `on_packet()` additionally assumes every packet is well-formed and addressed to this session — there's no demultiplexing by discriminator, which real BFD relies on to route packets to the right session at all.

## Code Landmarks

### `on_packet()`'s docstring table

Five lines, cheapest case first: `DOWN+DOWN -> INIT`, `DOWN+INIT -> UP`, `INIT+INIT -> UP`, `INIT+UP -> UP`, everything else unchanged. This is RFC 5880 Section 6.2's three-way handshake compressed into one ordered `if`/`elif` chain — reading the docstring before the code tells you what each branch is *for* before you read what it *does*.

### The two unconditional lines at the top of `on_packet()`

`session.remote_state_last_heard = remote_state` and `session.last_packet_at = now` run before any of the state-transition branches, every single call. Even a packet that doesn't advance `local_state` still updates what the session knows about the peer and resets the silence clock — a packet that "does nothing" to the state machine still counts as proof of life.

### `check_timeout()`'s single branch

Loss of the peer never passes through `INIT` — `local_state` goes straight to `DOWN`. Contrast this with `on_packet()`'s graduated climb (`DOWN -> INIT -> UP`, sometimes two calls): going up is negotiated in one or two steps, going down is immediate and total.

### `detection_time()`

`detect_multiplier * interval_ms` — one multiplication, no addition, no skew. Unlike VRRP's `master_down_interval()`, there's no per-session variation analogous to priority; every BFD session's detection budget depends only on its own configured multiplier and interval.

## Failure Questions

Use the source file to answer these:

1. A session starts with `local_state=DOWN` and receives a packet reporting `remote_state=UP`. Which branch of `on_packet()` fires, and what does `local_state` become? Is this combination even listed as one of the four transition branches?
2. `on_packet()`'s branches check `INIT + remote in (INIT, UP)` but there is no branch for `UP + remote DOWN`. What does `local_state` do in that case, and which line in the function is responsible for that outcome?
3. `check_timeout()` never sets `local_state` to `INIT`. Given the three `BfdState` values, is `INIT` reachable at all from `check_timeout()`, or only from `on_packet()`?
4. For `detect_multiplier=3` and `interval_ms=50`, what does `detection_time()` return? At exactly that many milliseconds of silence, does `check_timeout()` change `local_state`, or does it need one more millisecond?
5. `on_packet()` updates `last_packet_at` on every call, including calls that fall into the "anything else, unchanged" branch. Why does even a packet that doesn't change `local_state` still reset the timeout clock that `check_timeout()` reads?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/ha/session_03_walkthrough.py
```

The walkthrough drives one session through `DOWN -> INIT -> UP` step by step, shows a session that reaches `UP` via the direct `DOWN + remote INIT` path, computes `detection_time()` from `detect_multiplier=3` and `interval_ms=50`, and checks `check_timeout()` one millisecond before and exactly at that threshold.

## Done When

The learner can say all of the following without looking at notes:

- "BfdSession negotiates in both directions — local_state only climbs as far as what the peer last reported."
- "Going up is graduated through INIT; going down from silence is immediate, straight to DOWN."
- "detection_time is detect_multiplier times interval_ms, and check_timeout uses the same >= boundary convention as VRRP's silence check."

## References

- RFC 5880 Section 6.2 (State Variables, the three-way handshake table)
- RFC 5880 Section 6.8.4 (Detection Time calculation)
