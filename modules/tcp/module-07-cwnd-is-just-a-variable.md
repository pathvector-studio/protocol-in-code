# Session 07 / Module 07: cwnd Is Just a Variable

## Position

- Track: TCP
- Session: 07
- Site lesson: `pathvector-site/courses/protocols-in-code/tcp/module-07/index.html`
- Source file: `src/protocol_in_code/tcp/congestion.py`
- Walkthrough script: `examples/tcp/session_07_walkthrough.py`

## Core Question

Congestion control has a reputation for being an algorithm. Read as code, is it anything more than a handful of rules for moving one integer up or down?

## Outcome

By the end of this session, the learner should be able to:

- state the one comparison that decides slow start versus congestion avoidance
- explain why slow start grows cwnd by one MSS per ack rather than doubling it directly
- explain why congestion avoidance needs a full `cwnd` acks before growing by one MSS
- contrast what a timeout does to `cwnd` and `ssthresh` against what fast retransmit does, starting from the same state

## Read Order

1. Read `INITIAL_CWND`
2. Read `CongestionPhase`
3. Read `CongestionState`
4. Read `phase()`
5. Read `on_ack()`
6. Read `on_timeout()`
7. Read `on_fast_retransmit()`
8. Run `examples/tcp/session_07_walkthrough.py`

## Read It Like Code

```python
CongestionState(
    cwnd,
    ssthresh,
    acks_in_round,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `cwnd` | The congestion window, in MSS units (an integer count of segments, not bytes). This is the number everything else exists to move. |
| `ssthresh` | The slow-start threshold. Not a hard cap — it's the boundary `phase()` compares `cwnd` against. |
| `acks_in_round` | A counter that only matters in congestion avoidance. It's how the code counts "a full cwnd's worth of acks" without doing any division or fractional math. |

## Decision Flow

```text
phase():
    cwnd < ssthresh   -> SLOW_START
    cwnd >= ssthresh  -> CONGESTION_AVOIDANCE

on_ack(), phase computed first:
    SLOW_START            -> cwnd += 1, acks_in_round reset to 0
    CONGESTION_AVOIDANCE  -> acks_in_round += 1
                              acks_in_round >= cwnd  -> cwnd += 1, acks_in_round reset to 0

on_timeout()          -> ssthresh = max(cwnd // 2, 2); cwnd = 1;          acks_in_round = 0
on_fast_retransmit()  -> ssthresh = max(cwnd // 2, 2); cwnd = ssthresh;  acks_in_round = 0
```

## Reading Lens

The important move in this session is to resist treating "congestion control" as one big black-box algorithm, and instead ask, for each function:

- which field does this function read to decide what to do?
- which field(s) does it write, and in what order?
- is `phase()` being called fresh each time, or is the phase cached anywhere? (It's recomputed from `cwnd` and `ssthresh` every time — there is no stored phase field.)
- when `cwnd == ssthresh` exactly, which branch of `phase()` fires?

## Toy Model Boundary

RFC 5681's real fast recovery inflates `cwnd` further for each additional duplicate ack received while recovering (to account for the segments that have left the network), then deflates back to `ssthresh` once the retransmission is acked. This toy's `on_fast_retransmit()` skips the inflation entirely and jumps straight to `cwnd = ssthresh` in one call — there's no in-recovery state at all, and no distinction between "just entered recovery" and "still in recovery."

Slow start here also grows by exactly one MSS per acked segment, which produces a doubling of `cwnd` per round trip only if every segment in that round trip gets acked (and every ack is processed as a separate `on_ack()` call) — the code itself has no notion of "round trip," only a running count of individual acks. There's no delayed-ack accounting, no ECN, and cwnd is unitless MSS counts rather than bytes, so this toy also skips the byte-counting variant of congestion avoidance that real stacks often use.

## Code Landmarks

### `CongestionState`

Three integers. `cwnd` starts at `INITIAL_CWND = 1`; `ssthresh` starts at 64 as an arbitrary "assume a decently sized network" default. `acks_in_round` starts at 0 and is meaningless outside congestion avoidance.

### `phase()`

One comparison, `cwnd < ssthresh`. This function has no side effects and is called fresh by both `on_ack()` (to decide which branch to take) and by anything inspecting the state externally — there is no cached phase anywhere in `CongestionState`.

### `on_ack()`

The reading target. It calls `phase()` once, at the top, and dispatches on the result. In `SLOW_START`, growth is unconditional: `cwnd += 1` on every single ack, with `acks_in_round` reset to 0 defensively even though it wasn't being used. In `CONGESTION_AVOIDANCE`, growth is gated: `acks_in_round` increments every ack, but `cwnd` only grows once `acks_in_round >= cwnd` — read this as "wait for a whole window's worth of acks," not as any per-ack fractional increment.

### `on_timeout()` vs `on_fast_retransmit()`

Both compute the exact same new `ssthresh`: `max(cwnd // 2, 2)`. They diverge only on where `cwnd` lands afterward — `on_timeout()` drops it all the way to `INITIAL_CWND` (1), while `on_fast_retransmit()` sets it to the just-computed `ssthresh`. Same halving, very different landing point for `cwnd`.

## Failure Questions

Use the source file to answer these:

1. When `cwnd == ssthresh` exactly, which phase does `phase()` report, and which comparison operator makes that true?
2. In congestion avoidance, if `cwnd = 4` and `acks_in_round = 3`, what does the next `on_ack()` call do to both fields? What if `acks_in_round` had been 2 instead?
3. Starting from `CongestionState(cwnd=10, ssthresh=20)`, what are `cwnd` and `ssthresh` after `on_timeout()`? What are they after `on_fast_retransmit()` instead, from that same starting state? Which field ends up identical in both outcomes?
4. `on_timeout()` sets `ssthresh = max(cwnd // 2, 2)`. If `cwnd` is 2 or 3 at the moment of timeout, what does `ssthresh` become, and which term in the `max()` is doing the work?
5. In `SLOW_START`, does `on_ack()` ever read or update `acks_in_round` for a reason other than resetting it? What does that imply about whether slow-start growth depends on that field at all?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tcp/session_07_walkthrough.py
```

The walkthrough grows `cwnd` one ack at a time through slow start up to the `ssthresh` boundary, shows the phase flip and the ack-counting behavior of congestion avoidance, then branches the *same* starting state into a timeout path and a fast-retransmit path to contrast where each leaves `cwnd`.

## Done When

The learner can say all of the following without looking at notes:

- "`phase()` is one comparison, recomputed every time, never cached."
- "Slow start adds one MSS per ack; congestion avoidance adds one MSS per full `cwnd` acks, tracked by an explicit counter, not division."
- "Timeout and fast retransmit compute the same new `ssthresh`, but timeout drops `cwnd` to 1 while fast retransmit keeps it at the new `ssthresh`."

## References

- RFC 5681 Section 2 (definitions: MSS-based cwnd and ssthresh)
- RFC 5681 Section 3.1 (slow start and congestion avoidance)
- RFC 5681 Section 3.2 (fast retransmit / fast recovery)
