# Session 02 / Module 02: Stratum Is Depth in a Tree

## Position

- Track: NTP
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/ntp/module-02/index.html`
- Source file: `src/protocol_in_code/ntp/stratum.py`
- Walkthrough script: `examples/ntp/session_02_walkthrough.py`

## Core Question

Every NTP server advertises a stratum number. What is that number actually counting, and why does a client prefer a lower one even when it means a longer round trip?

## Outcome

By the end of this session, the learner should be able to:

- state what stratum 1 means and why it is the root, not a client-visible detail of some other server
- compute `advertised_stratum()` for any upstream value, including past the cap
- explain why `usable()` treats 16 specially instead of just checking a maximum
- explain both branches of `prefer()` and justify the tie-break order

## Read Order

1. Read the module docstring
2. Read the three constants
3. Read `Candidate`
4. Read `advertised_stratum()`
5. Read `usable()`
6. Read `prefer()`
7. Run `examples/ntp/session_02_walkthrough.py`

## Read It Like Code

```python
Candidate(
    server,
    stratum,
    delay_ms,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `server` | Identity only -- nothing in this module inspects it except to report a winner. |
| `stratum` | Distance from a reference clock, in hops. `prefer()`'s primary sort key. |
| `delay_ms` | Round-trip delay for this candidate, from `offset.delay()`. `prefer()`'s tie-break key. |

## Decision Flow

```text
advertised_stratum(upstream):
  upstream + 1 <= 16   -> upstream + 1
  upstream + 1 >  16   -> 16   (never advertise worse than "unsynchronized")

usable(candidate):
  1 <= stratum <= 15    -> True
  stratum == 16          -> False   (or anything else outside 1..15)

prefer(a, b):
  a.stratum != b.stratum  -> whichever has the lower stratum
  a.stratum == b.stratum  -> whichever has the lower (or equal) delay_ms
```

## Reading Lens

The important move in this session is to stop reading stratum as a quality score and start reading it as a hop count, the same way you read RIP's metric:

- how many servers sit between this candidate and an actual reference clock?
- when `advertised_stratum()` adds 1, is that visible to the client the way an incremented RIP metric is visible to a downstream router?
- what does hitting the cap (16) actually communicate, versus what a client might assume it means?

## Toy Model Boundary

Real NTP does not pick "the" server this way in isolation -- RFC 5905's clock selection and clustering algorithms combine stratum, delay, and several statistical outlier checks across multiple simultaneous servers to build a weighted combination, not a single winner from a two-way `prefer()`. This module also has no notion of a server actually holding a reference clock (no GPS, no atomic standard object) -- `STRATUM_REFERENCE = 1` is just a number a `Candidate` can carry. There is no leap second or leap indicator field here either; stratum in this toy is pure integer depth, nothing else.

## Code Landmarks

### `advertised_stratum()`

`min(upstream_stratum + 1, STRATUM_UNSYNC)`. One increment, one cap. Cross-reference: `rip/update.py`'s route-update loop computes `clamp_metric(advertised_metric + 1)` for exactly the same reason -- a router (or here, an NTP server) tells its downstream neighbors "one hop further than what I was told," and both protocols cap that number rather than let it grow without bound. Same hop-count arithmetic, applied to two different resources: RIP counts distance from a prefix's origin, NTP counts distance from a working clock.

### `usable()`

`STRATUM_REFERENCE <= candidate.stratum <= STRATUM_MAX`. Written as a range check, not `stratum != 16`, because nothing in this module's type system stops a `Candidate` from carrying a nonsensical stratum like `0` or `-5` or `200` -- the range check treats all of those the same as `16`: not usable.

### `prefer()`

Two-level comparison, stratum first. Read the docstring's parenthetical carefully: delay does not appear in `theta`'s formula directly (see `offset.py`), but a smaller delay bounds how long the symmetry assumption had to hold, which is why it is a reasonable second-place tie-break rather than an arbitrary one.

## Failure Questions

Use the source file to answer these:

1. `advertised_stratum(15)` and `advertised_stratum(20)` both return 16. What real-world difference between those two upstream servers does the client lose the ability to see once both advertise 16?
2. Why does `usable()` check a lower bound (`STRATUM_REFERENCE`) at all -- what would have to be true of a `Candidate` for `usable()` to reject it for being too low rather than too high?
3. `prefer()`'s tie-break compares `a.delay_ms <= b.delay_ms`, not `<`. If `a` and `b` have identical stratum and identical delay, which one does `prefer()` return, and does that choice matter for anything downstream in this module?
4. The docstring for `prefer()` says a smaller delay means "less room for the symmetry assumption to be wrong in practice." Looking only at `offset.py`, does a smaller `delay_ms` prove the path was symmetric? What is the actual relationship?
5. If `advertised_stratum()` did not cap at `STRATUM_UNSYNC`, what value would a chain of five servers, each one hop past a client that queries stratum-13 upstream, eventually advertise -- and why would that number stop meaning "hops from a reference clock"?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/ntp/session_02_walkthrough.py
```

The walkthrough advertises from stratum 1 (one visible hop of growth), then caps from both 15 and 20 to confirm the cap is a ceiling, not a wraparound; checks `usable()` at the 15/16 boundary; and runs `prefer()` twice -- once where a lower-stratum, higher-delay candidate wins, once where equal-stratum candidates are decided purely by delay.

## Done When

The learner can say all of the following without looking at notes:

- "Stratum is a hop count from a reference clock, computed the same way RIP computes a route's metric."
- "16 is not just a big number -- it is the specific value that means unsynchronized, and the cap exists so a server never advertises anything worse."
- "`prefer()` decides on stratum first and delay only breaks a tie -- fewer hops beats a shorter round trip."

## References

- RFC 5905 Section 7.3 (Peer Process, stratum field and its use)
