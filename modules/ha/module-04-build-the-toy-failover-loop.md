# Session 04 / Module 04: Build the Toy Failover Loop

## Position

- Track: HA (VRRP+BFD)
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/ha/module-04/index.html`
- Source file: `src/protocol_in_code/ha/failover_loop.py`
- Walkthrough script: `examples/ha/session_04_walkthrough.py`

## Core Question

A real HA pair runs both a millisecond-scale detector and a seconds-scale one, watching the same failure at once — what does it actually look like when both are wired to the same pair of routers?

## Outcome

By the end of this session, the learner should be able to:

- name every field on `ToyHaPair` and which earlier session's module owns the thing it holds
- explain why `tick()` checks BFD before VRRP, and why VRRP's check still runs even after BFD has already flipped ownership
- point at the two trace lines that demonstrate the two-timescale gap and read off both timestamps
- trace `master_returns()` and say, for both settings of `preempt_enabled`, who ends up owning the virtual IP

## Read Order

1. Read the module docstring at the top of the file
2. Read `ToyHaPair`'s field list top to bottom
3. Read `ToyHaPair.__post_init__`
4. Read `tick()`
5. Read `_promote()`
6. Read `advertisement_received()`
7. Read `master_returns()`
8. Read `who_owns()`
9. Read `run_failover()`
10. Run `examples/ha/session_04_walkthrough.py`

## Read It Like Code

```python
ToyHaPair(
    master_router,
    backup_router,
    virtual_ip,
    preempt_enabled,
    master_watch,
    bfd_on_backup,
    clock,
    current_owner,
    trace,
)
```

## Parts List

Every field on `ToyHaPair` and every function `failover_loop.py` imports was taught by an earlier session in this track. The capstone's only new code is the wiring between them.

| Import | Session that taught it | What it contributes to `ToyHaPair` |
|---|---|---|
| `vrrp_election.VrrpRouter`, `should_preempt` | 01 | `master_router` and `backup_router`; `should_preempt()` is the entire decision inside `master_returns()`. |
| `vrrp_timeout.BackupWatch`, `heartbeat`, `master_is_down` | 02 | `master_watch`; `master_is_down()` is the seconds-scale half of `tick()`'s two checks. |
| `bfd.BfdSession`, `BfdState`, `on_packet`, `check_timeout` | 03 | `bfd_on_backup`; `check_timeout()` is the millisecond-scale half of `tick()`'s two checks, and `on_packet()` drives `advertisement_received()`. |

## Decision Flow

```text
tick(ms):
  clock += ms

  1. BFD, checked first (the faster detector):
       bfd_was_up = local_state is not DOWN
       new_state  = check_timeout(bfd_on_backup, clock)
       new_state is DOWN and bfd_was_up  -> trace "BFD detects peer down"
                                             if current_owner is master -> promote backup

  2. VRRP, checked second (the fallback, runs regardless of what BFD did):
       vrrp_was_up = not master_is_down(master_watch, priority, clock - ms)
       vrrp_was_up and master_is_down(master_watch, priority, clock)
                                          -> trace "VRRP master_down_interval elapsed"
                                             if current_owner is master -> promote backup
                                             (no-op if BFD already promoted it)

master_returns():
  advertisement_received()  (heartbeat + BFD UP packet)
  current owner is already master_router  -> return, nothing to do
  should_preempt(current, master_router, preempt_enabled)
       True  -> promote master_router, trace "preemption on"
       False -> trace "preemption off", current owner keeps it
```

## Reading Lens

The important move in this session is to stop reading `tick()` as "the failover function" and start asking, at every call:

- which detector's threshold did this `tick()` call cross — BFD's, VRRP's, both, or neither?
- is `current_owner` still the master by the time each check runs, or did an earlier check in the *same* `tick()` call already move it?
- what would `pair.trace` say if this were a real debugging session — does each line stand on its own without the surrounding code?

The two-timescale gap is the entire point of this file: BFD's `detection_time` is milliseconds (`3 * 50 = 150`), VRRP's `master_down_interval` is seconds (`3007` for priority 254). Both detectors are watching the exact same silence. BFD gets there first and moves ownership; VRRP's check still runs on every subsequent `tick()` and still crosses its own threshold later — traced as "would have promoted on its own" even though there's nothing left for it to do. Read both trace lines side by side and the gap becomes a concrete pair of numbers instead of a sentence in a design doc.

## Toy Model Boundary

`ToyHaPair` models exactly two routers and one virtual IP — no VRRP groups, no more than one backup, no scenario where a third router's advertisement has to be reconciled against the first two. `clock` is a single synchronous integer advanced only by explicit `tick()` calls from the caller; there is no wall clock, no jitter, no reordering, and `advertisement_received()` and `tick()` are never interleaved by anything other than the caller's own sequencing in `run_failover()`. Real deployments also run BFD and VRRP as genuinely independent asynchronous processes, each with its own scheduling jitter — this module's ticks are deterministic on purpose, which is what makes every timestamp in the walkthrough reproducible.

## Code Landmarks

### The module docstring

"BFD notices first and triggers the failover early, VRRP's own timer is the safety net that would have caught it anyway, just later." Read this before `tick()` — it's the thesis the rest of the file exists to demonstrate with real numbers instead of asserting in prose.

### `tick()`'s BFD-then-VRRP ordering

The comment above `tick()` states the reason directly: BFD is the faster detector, so if it has already declared the peer down, ownership has already flipped by the time VRRP's check even runs in the same call. VRRP's check runs unconditionally anyway — `_promote()` is idempotent in effect because the `if self.current_owner == self.master_router.name` guard makes the second promotion attempt a no-op once BFD has already moved it.

### `_promote()`

Two lines: set `current_owner`, append one trace line stamped with the current `clock`. Every ownership change in this file, whether triggered by BFD, VRRP, or `master_returns()`, goes through this one function — the trace format never has to be kept in sync by hand across three call sites.

### `master_returns()`'s early return

`if current.name == self.master_router.name: return`. If the master never actually lost ownership (BFD and VRRP both stayed quiet), `master_returns()` has nothing to decide — `should_preempt()` is never even called. This guard is what keeps `master_returns()` a no-op in a steady-state pair.

### `run_failover()`'s comment before the tick loop

"Advance in small steps past BOTH thresholds... confirming the fallback detector would have caught the failure anyway." The choice of `ms=50` per tick, 80 times, is not arbitrary — it's small enough to land exactly on BFD's 150ms threshold and land the walk cleanly past VRRP's ~3007ms one within the same loop.

## Failure Questions

Use the source file to answer these:

1. `tick()` checks BFD's `check_timeout()` before VRRP's `master_is_down()`. If a single `tick(ms=...)` call is large enough to cross both thresholds at once, does VRRP's check still append its own trace line, or does BFD's earlier promotion suppress it?
2. `_promote()` is called from inside both the BFD branch and the VRRP branch of `tick()`. What guard keeps the VRRP branch from re-appending a trace line and re-promoting a router that BFD already promoted in the same `tick()` call?
3. `master_returns()` calls `advertisement_received()` unconditionally, even when the master never lost ownership. What are the two side effects of that call, and do either of them matter if `current_owner` is already `master_router.name`?
4. `who_owns()` takes a `virtual_ip` argument and compares it against `self.virtual_ip`. What does it return if called with a different IP than the pair's own, and what does that tell you about how many virtual IPs one `ToyHaPair` is designed to track?
5. In `run_failover()`, the tick loop runs `range(80)` calls of `ms=50`, reaching `clock=4000` by the time `master_returns()` is called. Using `master_down_interval(254) == 3007` and `detection_time() == 150` from Sessions 02 and 03, which of the two detectors' thresholds does the loop cross first, and by how many ticks?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/ha/session_04_walkthrough.py
```

The walkthrough builds a `ToyHaPair` (priority 254 master, priority 100 backup), advances the clock in 50ms steps to reach BFD's `detection_time` and confirms `who_owns()` flips to the backup at `t=150ms`, continues to VRRP's `master_down_interval` and confirms that fallback line appears later at `t=3050ms` — with both trace lines and their ordering asserted together as the two-timescale headline — then calls `master_returns()` twice: once on a pair with `preempt_enabled=True` (the master takes the virtual IP back) and once with it `False` (the backup keeps it).

## Done When

The learner can say all of the following without looking at notes:

- "Every field on ToyHaPair belongs to an earlier session; this module only wires them together in tick() and master_returns()."
- "BFD is checked first because it's faster, but VRRP's check still runs every tick — it's the fallback that would have caught the failure on its own, just later."
- "The two-timescale gap is a real pair of numbers in the trace: BFD at ~150ms, VRRP at ~3000ms, for the exact same underlying silence."

## References

- RFC 5798 (VRRPv3) — composed with Session 01's election and Session 02's timeout
- RFC 5880 (BFD) — composed with Session 03's three-state negotiation
