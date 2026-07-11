# Session 06 / Module 06: Build the Toy Connection Janitor

## Position

- Track: TCP2
- Session: 06
- Site lesson: `pathvector-site/courses/protocols-in-code/tcp2/module-06/index.html`
- Source file: `src/protocol_in_code/tcp2/janitor_loop.py`
- Walkthrough script: `examples/tcp2/session_06_walkthrough.py`

## Core Question

None of TIME_WAIT, keepalive, or the backlog is the protocol itself — so what does one object look like whose entire job is running that housekeeping over a scripted day of connection churn?

## Outcome

By the end of this session, the learner should be able to:

- name every field on `ToyConnectionJanitor` and which earlier session's module owns the logic behind it
- trace `tick()`'s three-step order and explain why TIME_WAIT expiry runs before the idle-connection chase
- explain what triggers cookie-mode and what ends it
- run `run_day_in_the_life()` over a scripted mix of events and read the resulting trace as the record of every housekeeping decision made
- state, in one sentence, why this module is the track's capstone rather than another ordinary session

## Read Order

1. Read the module comment above `ToyConnectionJanitor` — the three books it keeps, and why
2. Read `EventKind` and `Event`
3. Read `ToyConnectionJanitor`'s field list
4. Read `enter_time_wait()` and `mark_active()`
5. Read `tick()`, then its three helpers in order: `_expire_time_wait()`, `_chase_idle_connections()`, `_report_backlog_pressure()`
6. Read `handle_syn()`, `handle_final_ack()`, `accept_one()`
7. Read `run_day_in_the_life()`
8. Run `examples/tcp2/session_06_walkthrough.py`

## Read It Like Code

```python
ToyConnectionJanitor(
    backlog,
    clock,
    time_wait_entries,
    idle_connections,
    probe_replies,
    cookie_mode,
    trace,
)
```

## Parts List

Every import in `janitor_loop.py` was taught by an earlier session in this course. The capstone's only new code is the dispatcher wiring them into one scripted day.

| Import | Session that taught it | What it contributes to `ToyConnectionJanitor` |
|---|---|---|
| `time_wait_cost.py` — `EPHEMERAL_PORTS`, `time_wait_slots`, `max_rate_to_one_destination` | tcp2 Session 01 | Prices the promise `tick()` enforces: every port sitting in `time_wait_entries` is one this module cannot hand back until `TWO_MSL` passes. |
| `syn_cookies.py` — `encode_cookie`, `verify_cookie`, `CookieVerdict` | tcp2 Session 02 | The real mechanism named in `_report_backlog_pressure()`'s trace line — this module only flips `cookie_mode` to `True`; it does not itself encode or verify a cookie. |
| `nagle_delack.py` — `simulate`, `Timeline` | tcp2 Session 03 | Not imported here directly; it belongs to the same "two reasonable rules interact badly" family as this module's housekeeping stories, but operates at the segment-timing layer this janitor never touches. |
| `keepalive.py` — `KEEPALIVE_COUNT`, `KeepaliveVerdict`, `connection_verdict` | tcp2 Session 04 | `_chase_idle_connections()`'s entire decision: whether an idle connection is still `PROBING` or has gone `DEAD`. |
| `backlog.py` — `AckOutcome`, `ListenBacklog`, `SynOutcome`, `app_accept`, `on_final_ack`, `on_syn` | tcp2 Session 05 | `self.backlog` itself, plus every function `handle_syn()`, `handle_final_ack()`, and `accept_one()` delegate to. |
| `tcp.teardown.time_wait_expired`, `TWO_MSL` | tcp Session 09 (track 1) | `_expire_time_wait()`'s only real logic — and the source of the promise this whole module is built to keep. See below. |

`tcp/teardown.py` (track 1, Session 09) is where the TIME_WAIT promise was first made: `on_segment_active()` moves a connection into `CloseState.TIME_WAIT` and stamps `wait_started_at`, and `time_wait_expired()` is the comparison that eventually resolves it. `janitor_loop.py` is where that promise gets collected on — `enter_time_wait()` and `_expire_time_wait()` are this module's side of the same contract, running against a clock instead of a single segment arrival.

## Decision Flow

```text
tick(seconds):
  1. self.clock += seconds
  2. _expire_time_wait()         # delete every time_wait_entries key past TWO_MSL, trace it
  3. _chase_idle_connections()   # per idle connection: PROBING -> record another unanswered
                                  # probe, or DEAD -> delete + clear its probe_replies, trace it
  4. _report_backlog_pressure()  # syn_queue at syn_limit and not yet cookie_mode -> engage it;
                                  # syn_queue back under syn_limit and cookie_mode -> disengage it

handle_syn(client_tuple):
  cookie_mode is True  -> answered statelessly, backlog untouched, trace "cookie-mode"
  otherwise             -> on_syn() against the real syn_queue, then re-check backlog pressure

handle_final_ack(client_tuple):
  on_final_ack() against the backlog
  MOVED_TO_ACCEPT_QUEUE -> mark_active() (this connection is now the janitor's to watch for idleness)
```

## Reading Lens

The important move in this session is to stop reading each housekeeping story in isolation and start asking, at every line of `tick()` and `run_day_in_the_life()`:

- which of the three books — `time_wait_entries`, `idle_connections`, or `backlog` — does this line touch, and is that the only book it touches?
- what order do `tick()`'s three helpers run in, and would swapping two of them change any test's outcome?
- what does `self.trace` say happened, and could a debugger reconstruct the whole day from `trace` alone without re-running anything?

This is also the moment to look back across the whole tcp2 track and the NAT track together: `nat/timeout.py` (NAT Session 05) and this module's `_expire_time_wait()` share the same "stamp a time, compare age to a limit at read time" shape as `dns/cache.py` and `tls/resumption.py` before it — and `keepalive.py` (tcp2 Session 04) is the same shape stretched to 7200 seconds, arriving too late to save a NAT mapping that used the 30-second version of this exact idea. None of the three books this janitor keeps is protocol logic. TIME_WAIT is bookkeeping about a port, not a segment. Keepalive is bookkeeping about silence, not data. The backlog is bookkeeping about two queues an application and a kernel each own half of. The capstone's thesis, stated directly in the module's own docstring: none of this is the protocol — it is the housekeeping the protocol leaves behind.

## Toy Model Boundary

`tick(seconds)` is a single synchronous call that advances the clock and runs all three housekeeping passes atomically — a real kernel runs TIME_WAIT expiry, keepalive probing, and SYN-queue pressure checks on independent timers that can interleave with arriving packets at any instant, not in one blocking sweep. `_chase_idle_connections()` records at most one unanswered probe per `tick()` call regardless of how many `KEEPALIVE_INTERVAL`-sized gaps that `tick()`'s `seconds` actually spans — ticking in large jumps can skip past probes a finer-grained clock would have fired individually (this module's own walkthrough ticks in `KEEPALIVE_INTERVAL`-sized steps once probing starts, precisely to avoid that skip). `_report_backlog_pressure()` is a binary `cookie_mode` flag flipped by one connection janitor; it does not itself run `syn_cookies.py`'s `encode_cookie()`/`verify_cookie()` — a real cookie-mode implementation would replace `on_syn()`'s queuing entirely, not just narrate it in a trace line. There is one listen socket and one clock; nothing here models multiple sockets, multiple network interfaces, or real wall-clock drift.

## Code Landmarks

### The module comment above `ToyConnectionJanitor`

"Three books get kept, and each is kept for a different reason" — read this before the field list. It is the map for everything that follows.

### `tick()`

Three lines, three helpers, one order: expire TIME_WAIT, then chase idle connections, then report backlog pressure. `_expire_time_wait()` runs first because freeing a port has no dependency on the other two books.

### `_chase_idle_connections()`

The bridge to `keepalive.py`: `connection_verdict()` is asked fresh on every tick, fed whatever `probe_replies` have accumulated so far. This file does not compute a verdict once and cache it — every `tick()` re-derives it.

### `run_day_in_the_life()`'s docstring

"This is the capstone's whole point: nothing below is protocol logic." Read this before the three `EventKind` branches — it explains why the function is a plain dispatcher and nothing more.

## Failure Questions

Use the source file to answer these:

1. `tick()` calls `_expire_time_wait()`, then `_chase_idle_connections()`, then `_report_backlog_pressure()`, in that fixed order. Which of the three, if any, depends on a book that an earlier helper in the same `tick()` call might have just changed?
2. A connection's `last_activity` is such that its ninth keepalive probe time falls in the *middle* of a `tick(seconds)` call that jumps the clock across it in one step. Does `_chase_idle_connections()` still record all nine probes individually, or does it collapse them? What line answers this?
3. `_report_backlog_pressure()` checks `len(self.backlog.syn_queue) >= self.backlog.syn_limit and not self.cookie_mode` to engage cookie-mode. What has to become true for `elif` branch to disengage it later, and which function besides `tick()` also calls `_report_backlog_pressure()`?
4. `handle_final_ack()` calls `mark_active()` only when the outcome is `MOVED_TO_ACCEPT_QUEUE`. What happens to a connection's presence in `idle_connections` if `on_final_ack()` instead returns `ACCEPT_QUEUE_FULL`?
5. `EventKind.SYN_FLOOD_BURST`'s handling in `run_day_in_the_life()` never calls `handle_final_ack()` for any of the flood's SYNs. What book, if any, ends up holding an entry for those connections once the burst finishes?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tcp2/session_06_walkthrough.py
```

The walkthrough builds one `ToyConnectionJanitor` and runs `run_day_in_the_life()` over a scripted mix of `CONNECT_AND_CLOSE`, `IDLE_SILENCE`, and `SYN_FLOOD_BURST` events, then ticks the clock forward and checks the trace directly: TIME_WAIT expiring and freeing ports at `clock=300`, an idle connection declared DEAD at `clock=7875` after nine unanswered keepalive probes, and cookie-mode engaging once a SYN flood pushes `syn_queue` to its limit. It confirms `time_wait_entries` is empty after expiry and closes on a label quoting the capstone thesis.

## Done When

The learner can say all of the following without looking at notes:

- "ToyConnectionJanitor keeps three books — time_wait_entries, idle_connections, and backlog — and tick() runs one housekeeping pass over all three, in a fixed order."
- "TIME_WAIT expiry, keepalive, and the backlog's two queues are all this same shape: stamp a time or a count, compare it to a limit, act on the comparison."
- "None of this is the protocol — it is the housekeeping the protocol leaves behind."

## References

- This session composes the track: RFC 1122 Section 4.2.3.6 (keepalive, Session 04), the Linux/BSD listen-backlog behavior (Session 05, no single RFC), and `tcp/teardown.py`'s TIME_WAIT contract (track 1, Session 09, itself following RFC 9293 Section 3.5).
