# Session 04 / Module 04: Build the Toy NTP Client Loop

## Position

- Track: NTP
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/ntp/module-04/index.html`
- Source file: `src/protocol_in_code/ntp/client_loop.py`
- Walkthrough script: `examples/ntp/session_04_walkthrough.py`

## Core Question

Given several exchanges with a server (or servers), how does a real client decide which sample to trust, and how does it apply that sample's correction without risking a dangerous jump?

## Outcome

By the end of this session, the learner should be able to:

- name every function `client_loop.py` calls into from `offset.py`, and what each contributes
- explain why `best_sample()` minimizes delay, not offset or absolute offset
- compute `apply_correction()`'s clamped result for both a small and a large offset
- trace `run_sync()`'s full sequence of trace lines for a mixed batch of valid and malformed exchanges

## Read Order

1. Read the module docstring
2. Read `MAX_SLEW_PER_ADJUST`
3. Read `Sample`
4. Read `ToySntpClient`
5. Read `sample()`
6. Read `best_sample()`
7. Read `apply_correction()`
8. Read `run_sync()`
9. Run `examples/ntp/session_04_walkthrough.py`

## Read It Like Code

```python
ToySntpClient(
    local_clock_ms,
    samples,
    trace,
)
```

## Parts List

Every function `client_loop.py` calls into was taught by an earlier session in this track. The capstone's only new code is the sampling, filtering, and correction logic wired around them.

| Import | Session that taught it | What it contributes to `client_loop.py` |
|---|---|---|
| `Exchange` | 01 | The four-timestamp unit every `Sample` wraps; constructed by the caller, not by this module. |
| `ExchangeValidity`, `validate_exchange` | 01 | `sample()`'s first check -- a `MALFORMED` exchange is rejected and traced, never turned into a `Sample`. |
| `offset` | 01 | `sample()` calls this to fill `Sample.offset_ms`; the value `apply_correction()` eventually clamps and applies. |
| `delay` | 01 | `sample()` calls this to fill `Sample.delay_ms`; the value `best_sample()` minimizes over. |

`stratum.py` (Session 02) and `asymmetry.py` (Session 03) are not imported by `client_loop.py` at all -- this module works with a single server's exchanges and does not select among multiple candidates by stratum, nor does it attempt to detect or correct for asymmetry. Their lessons are present here only as background: `best_sample()`'s docstring explicitly reasons about delay as a proxy for "the symmetry assumption probably held," which is Session 03's thesis applied to a filtering decision instead of an error calculation.

## Decision Flow

```text
sample(client, exchange):
  validate_exchange(exchange) is MALFORMED  -> trace "rejected: ...", return None
  otherwise                                  -> build Sample(offset, delay), append, trace, return it

best_sample(client):
  no samples   -> None
  otherwise    -> the Sample with the minimum delay_ms

apply_correction(client, chosen):
  |chosen.offset_ms| <= MAX_SLEW_PER_ADJUST  -> apply chosen.offset_ms in full (a slew)
  |chosen.offset_ms| >  MAX_SLEW_PER_ADJUST  -> apply +/- MAX_SLEW_PER_ADJUST only (clamped)

run_sync(client, exchanges):
  sample() every exchange
  chosen = best_sample(client)
  chosen is None  -> trace "sync abandoned: no valid samples", return None
  otherwise       -> trace the choice, apply_correction(), return chosen
```

## Reading Lens

The important move in this session is to stop reading each function as an isolated demo and start asking, at every call:

- which earlier session's function is doing the actual arithmetic on this line?
- is this a filtering decision (which sample to trust) or a correction decision (how hard to nudge the clock), and which function owns each?
- what does `client.trace` say happened, and would that trace alone tell a debugger why the clock ended up where it did?

## Toy Model Boundary

This client talks to one batch of exchanges per `run_sync()` call, all treated as candidates from what could be one or many servers -- there is no `stratum.prefer()` wired in here to choose between servers first, and no repeated polling loop with a poll interval that adapts (RFC 5905's poll exponent). `MAX_SLEW_PER_ADJUST = 100.0` is a single flat cap applied uniformly; real NTP's step-vs-slew threshold (commonly around 128ms) and its behavior of stepping the clock outright for very large offsets rather than slewing indefinitely are both simplified away -- this module always slews, never steps, it just clamps how much. There is no notion of multiple simultaneous servers being statistically combined (RFC 5905's clock selection and cluster algorithms) -- `best_sample()` picks one winner from one flat list by a single key.

## Code Landmarks

### `sample()`

The gate. `validate_exchange()` runs first, and a malformed exchange never becomes a `Sample` -- it is traced as `"rejected: {validity.value}"` and the function returns `None`, so a caller iterating over exchanges must be prepared for `None` back.

### `best_sample()`

`min(client.samples, key=lambda s: s.delay_ms)` -- minimum delay, not minimum `|offset_ms|` and not minimum `offset_ms`. The docstring is explicit about why: delay does not appear in `theta`'s formula directly, but it bounds how long a symmetric-path assumption had to hold to still be roughly true. A large delay is not itself an error in the offset -- it is a red flag that the offset might be wrong for reasons the exchange cannot reveal (see Session 03).

### `apply_correction()`

`max(-MAX_SLEW_PER_ADJUST, min(MAX_SLEW_PER_ADJUST, chosen.offset_ms))`. Read the comment on `MAX_SLEW_PER_ADJUST` directly: "a bigger correction gets clamped, not stepped." The clamp preserves the *direction* of the correction always, and the *magnitude* only when it is already within the cap -- it never flips sign and never applies more than the cap in one call.

### `run_sync()`

The full loop, traced at every stage: how many exchanges came in, one `sample:` or `rejected:` line per exchange, a `chosen:` line naming the minimum delay among valid samples, and one `apply:` line from `apply_correction()`. If every exchange is rejected, `run_sync()` traces `"sync abandoned: no valid samples"` and returns `None` without ever calling `apply_correction()`.

## Failure Questions

Use the source file to answer these:

1. `best_sample()` minimizes `delay_ms`. Why not minimize `abs(offset_ms)` instead -- what would go wrong if a client trusted whichever sample claimed the smallest correction rather than whichever sample had the shortest round trip?
2. `apply_correction()`'s clamp is `max(-MAX_SLEW_PER_ADJUST, min(MAX_SLEW_PER_ADJUST, chosen.offset_ms))`. For `chosen.offset_ms = -500.0`, what does this expression evaluate to, and which of the two nested calls (`max` or `min`) is the one that actually constrains it?
3. `sample()` calls `validate_exchange()` before calling `offset()` or `delay()` at all. What would `offset()` return for a malformed exchange if `sample()` did not check validity first, and why would that value be actively misleading rather than just unused?
4. `run_sync()` calls `best_sample(client)` using `client.samples`, not the `exchanges` tuple passed in. If two calls to `run_sync()` happen on the same `client` object, what samples does the second call's `best_sample()` consider?
5. The clamp in `apply_correction()` preserves sign and caps magnitude. Given `chosen.offset_ms = 100.0` exactly (equal to `MAX_SLEW_PER_ADJUST`), does the clamp change the value at all? What does that boundary case tell you about whether the cap is inclusive or exclusive?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/ntp/session_04_walkthrough.py
```

The walkthrough samples three exchanges with delays 40ms, 11ms, and 119ms and confirms `best_sample()` picks the 11ms one; applies a +10ms offset and confirms it lands on the clock in full; applies a +500ms offset and confirms it clamps to exactly `MAX_SLEW_PER_ADJUST` (100ms); and finally runs `run_sync()` end-to-end over a batch that mixes two valid exchanges with one malformed one, asserting both that the chosen sample has the minimum delay and that the trace contains the exact `"chosen: delay=11.0ms (minimum among valid samples)"` line alongside a `"rejected:"` line for the malformed exchange.

## Done When

The learner can say all of the following without looking at notes:

- "Every calculation in `client_loop.py` reuses `offset()`, `delay()`, and `validate_exchange()` from Session 01 -- this module only adds the decision of which sample to trust and how hard to correct toward it."
- "`best_sample()` picks minimum delay because delay is the client's only observable proxy for the symmetry assumption having held, not because low delay directly implies low offset error."
- "`apply_correction()` always moves the clock in the correction's true direction, but never by more than `MAX_SLEW_PER_ADJUST` in one call -- a slew, not a step."

## References

- RFC 5905 Section 8 (On-Wire Protocol / clock offset, round-trip delay, and the client sampling this module simplifies)
- RFC 4330 (Simple NTP), for the general shape of an SNTP client's single-sample request/reply loop that this module's `run_sync()` loosely follows
