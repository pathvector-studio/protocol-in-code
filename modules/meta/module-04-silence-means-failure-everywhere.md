# Session 04 / Module 04: Silence Means Failure, Everywhere

## Position

- Track: Same Shape
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/meta/module-04/index.html`
- Source file: `src/protocol_in_code/meta/silence.py`
- Walkthrough script: `examples/meta/session_04_walkthrough.py`

## Core Question

BFD, VRRP, TCP keepalive, and NAT conntrack all infer failure from the absence of a signal, after a deadline — so once every deadline is converted to the same unit, what does the size of the gap between them actually tell you about the eras these protocols were designed in?

## Outcome

By the end of this session, the learner should be able to:

- name all four protocols' detection times in milliseconds, from memory, in the right order
- explain what normalizes the four numbers onto one shared unit, and why that normalization is necessary before comparing them at all
- state the `timescale_spread()` headline number and what design assumption explains it
- explain why a stock TCP keepalive interacting with a NAT conntrack table is a timing bug waiting to happen, not a hypothetical

## Read Order

1. Read the module docstring at the top of `silence.py`
2. Read `SilenceDemo` and the comment on its `detection_time` field
3. Read `demonstrate_all()` stanza by stanza — BFD, then VRRP, then TCP keepalive, then NAT
4. Read `timescale_spread()` and its docstring
5. Cross-read `tcp2/keepalive.py`'s module comment, which this file's docstring paraphrases directly
6. Run `examples/meta/session_04_walkthrough.py`

## Read It Like Code

```python
SilenceDemo(
    protocol,
    threshold_description,
    detection_time,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `protocol` | Which of the four real packages this row describes — `bfd`, `vrrp`, `tcp_keepalive`, or `nat_udp`. |
| `threshold_description` | The literal arithmetic that produced `detection_time`, in the package's own terms — a multiplier and an interval, or an idle time plus a probe schedule. |
| `detection_time` | Milliseconds until the protocol concludes the peer is gone. `MS_PER_SECOND` is the only thing standing between a second-native package and this shared field. |

## Decision Flow

```text
demonstrate_all(), each stanza calls the package's own real timing function, then normalizes to ms:
  bfd:           detect_multiplier(3) * interval_ms(50)                        = 150 ms       (native ms)
  vrrp:          master_down_interval(priority=100)                            = 3,609 ms      (native ms)
  tcp_keepalive: probe_times(0)[-1] * MS_PER_SECOND                            = 7,800,000 ms  (native seconds)
  nat_udp:       EXPIRY_SECONDS["udp"] * MS_PER_SECOND                         = 30,000 ms     (native seconds)

timescale_spread():
  (min(all four detection_time values), max(all four detection_time values)) = (150, 7_800_000)
```

## Reading Lens

The important move in this session is to stop reading each stanza's number in isolation and start asking:

- was this protocol's native unit milliseconds or seconds — and did I check `MS_PER_SECOND` was actually applied before comparing it to the others?
- what real-world deadline was this number tuned against — a human noticing a stall, or a leased line that never dropped?
- if this protocol's timeout outlives the middlebox state it depends on (as `tcp2/keepalive.py`'s own module comment says about NAT), what happens to the connection in the gap?

The four numbers, once normalized, span almost five orders of magnitude. That spread is the entire content of this session — everything else is where each number came from.

## Toy Model Boundary

`demonstrate_all()` calls four real timing functions with one hand-picked input each (a `BfdSession` with `interval_ms=50`, `priority=100` for VRRP, a keepalive schedule starting at `last_activity=0`, and the fixed `EXPIRY_SECONDS["udp"]` constant) — it is not a survey of every valid configuration these protocols support. BFD's interval and multiplier are both tunable per session; VRRP's `master_down_interval` depends on `priority`, so a different priority than 100 produces a different number; NAT conntrack UDP timeouts are implementation-specific and this course's `EXPIRY_SECONDS` is a toy constant, not a value pulled from any particular vendor's default. The headline spread (150ms to 7.8M ms) is real for *these* four inputs; it would shift, though probably not by an order of magnitude, for other reasonable inputs.

## Code Landmarks

### The module docstring

States the shared inference before any code runs: "absence of evidence, after a deadline, becomes evidence of absence. What differs is only the deadline's scale." The rest of the file is that one sentence, made concrete four times.

### `MS_PER_SECOND` and where it's applied

BFD and VRRP's underlying functions (`detection_time()`, `master_down_interval()`) already return milliseconds — no conversion needed. TCP keepalive and NAT UDP's underlying values (`probe_times()`, `EXPIRY_SECONDS`) are native seconds, so the stanza multiplies by `MS_PER_SECOND` before appending the row. Missing this multiplication on either of the second two stanzas would silently make TCP keepalive look 1000x faster than BFD instead of over 50,000x slower.

### The TCP keepalive stanza's `probe_times(...)[-1]`

Detection time isn't `KEEPALIVE_IDLE` alone — it's the clock time of the *last* probe in the schedule, taken from index `[-1]` of the tuple `probe_times()` returns. The comment above the stanza spells out the arithmetic: idle time, then `interval * (count - 1)` more seconds for the remaining probes to fire and go unanswered.

### `timescale_spread()`'s docstring

Names the punchline as history, not just arithmetic: "BFD's 150ms is tuned to catch a dead peer inside the time a human notices a stall, while stock TCP keepalive's default sits almost five orders of magnitude higher — tuned for an era of dedicated leased lines, long before NAT middleboxes routinely reclaimed idle mappings in under a minute." The comparison to `nat/timeout.py` is made explicit in the same sentence.

## Failure Questions

Use the source file to answer these:

1. Which two of the four `SilenceDemo` rows are computed by a function that already returns milliseconds natively, and which two require multiplying by `MS_PER_SECOND` — what would happen to `timescale_spread()`'s returned tuple if that multiplication were skipped for just the NAT row?
2. Why does the TCP keepalive stanza read `probe_times(last_activity=0)[-1]` instead of just using `KEEPALIVE_IDLE` directly — what would the resulting `detection_time` be off by, and in which direction?
3. `master_down_interval(priority=100)` returns 3,609. Using the formula in `threshold_description`, what would this session's VRRP row show for `priority=254` instead, and would it be larger or smaller than 3,609?
4. `timescale_spread()` returns a 2-tuple of `(min, max)`. Which protocol contributes the min, which contributes the max, and are those the same two protocols whose *native* unit was already milliseconds versus seconds?
5. The module docstring says NAT middleboxes reclaim idle mappings "in under a minute" while a stock TCP keepalive doesn't even start probing for `KEEPALIVE_IDLE` (2 hours). Using this session's NAT row and TCP keepalive row, by how many milliseconds does the NAT conntrack timeout expire *before* the first keepalive probe would even fire?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/meta/session_04_walkthrough.py
```

The walkthrough calls `demonstrate_all()`, checks it returns exactly 4 rows, asserts the four exact millisecond values (150 for BFD, 3,609 for VRRP, 30,000 for NAT UDP, 7,800,000 for TCP keepalive), confirms `timescale_spread() == (150, 7800000)`, and prints the orders-of-magnitude ratio between the two (52,000x).

## Done When

The learner can say all of the following without looking at notes:

- "BFD, VRRP, TCP keepalive, and NAT conntrack all infer failure from silence past a deadline — the mechanism is identical, only the deadline's size differs."
- "Once normalized to milliseconds, the four detection times span 150ms to 7.8 million ms — nearly five orders of magnitude."
- "A stock TCP keepalive is tuned for an era before NAT middleboxes existed, so it routinely arrives to find the conntrack mapping it was supposed to keep alive already gone."

## References

- `modules/ha/module-03-three-states-both-directions.md` — BFD session state, timed out via `detection_time()`
- `modules/ha/module-02-silence-means-failure.md` — VRRP's `master_down_interval()`, the session this track's title borrows from directly
- `modules/tcp2/module-04-keepalive-probes-an-idle-line.md` — TCP keepalive's probe schedule
- `modules/nat/module-05-state-expires-again.md` — NAT conntrack's per-protocol `EXPIRY_SECONDS`
