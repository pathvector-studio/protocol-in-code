# Session 03 / Module 03: Symmetry Is an Assumption

## Position

- Track: NTP
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/ntp/module-03/index.html`
- Source file: `src/protocol_in_code/ntp/asymmetry.py`
- Walkthrough script: `examples/ntp/session_03_walkthrough.py`

## Core Question

`offset()` assumes the outbound and return delays are equal. When they are not, exactly how wrong does the reported offset get -- and can the protocol ever tell?

## Outcome

By the end of this session, the learner should be able to:

- state the exact formula for the error asymmetry introduces, in terms of forward and backward delay
- explain the sign of that error: which direction (forward-heavy or backward-heavy) biases the report which way
- use `build_exchange()` to go from known ground truth to the four timestamps `offset()` would see
- explain, precisely, why nothing in `t1..t4` can reveal `forward_ms` and `backward_ms` separately

## Read Order

1. Read the module docstring's re-derivation against known ground truth
2. Read `true_offset_error()`
3. Read `build_exchange()`
4. Re-read `offset.py`'s `offset()` with this file's docstring in mind
5. Run `examples/ntp/session_03_walkthrough.py`

## Read It Like Code

```python
build_exchange(
    true_offset_ms,
    forward_ms,
    backward_ms,
    server_processing_ms,
    t1,
) -> Exchange
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `true_offset_ms` | Ground truth `theta` -- known only to the simulator, never to `offset()`. |
| `forward_ms` | True one-way client-to-server delay, `d_f`. Can differ from `backward_ms`. |
| `backward_ms` | True one-way server-to-client delay, `d_b`. The asymmetry is `d_b - d_f`. |
| `server_processing_ms` | Time added between `t2` and `t3`; irrelevant to offset error, present for realism. |

## Decision Flow

```text
forward_ms == backward_ms   -> offset() reports true_offset_ms exactly
forward_ms != backward_ms   -> offset() reports true_offset_ms - (backward_ms - forward_ms) / 2
                                (error = true - report = (backward_ms - forward_ms) / 2)
```

## Reading Lens

The important move in this session is to stop asking "is the reported offset correct?" and start asking:

- what quantity does `offset()`'s derivation need to cancel to isolate `theta`, and what does it assume about `d_out` and `d_in` to make that cancellation exact?
- given only `t1..t4`, can you recover `forward_ms` and `backward_ms` separately, or only their sum?
- when the return leg is slower, which direction does the client's belief about the server's clock move -- ahead or behind truth -- and why does that match "queuing gets misread as skew"?

## Toy Model Boundary

`build_exchange()` is explicitly a simulator, not a protocol step -- real NTP never has access to `true_offset_ms`, `forward_ms`, or `backward_ms` as separate quantities; those exist here only so the walkthrough can compare a report to ground truth. This module also does not model why a path becomes asymmetric (route changes, queuing, physical layer differences) -- `forward_ms` and `backward_ms` are given, not derived from any network model. There is no correction mechanism here either; this file only measures the damage, it does not propose a fix (the closest a real client comes is minimum-delay filtering, covered in Session 04).

## Code Landmarks

### The module docstring's re-derivation

Walks the same two equations from `offset.py` but keeps `d_out` and `d_in` separate instead of assuming they're equal, landing on `reported_offset = theta - (d_b - d_f) / 2`. Read this line by line against `offset.py`'s derivation -- it is the same algebra, just without the simplifying assumption plugged in early.

### `true_offset_error()`

`(backward_ms - forward_ms) / 2`. This is `true_offset - reported_offset`, not the other way around -- the function is named for what it returns (the error), and the sign matters: a positive value means the report understated (or overstated, depending on which side of zero `theta` sits on) relative to truth by exactly that much. The docstring is explicit that this is "half the gap between the return delay and the forward delay," and the walkthrough asserts `reported + error == truth` as the identity that pins the sign down unambiguously.

### `build_exchange()`

`t2 = t1 + forward_ms + true_offset_ms` and `t4 = t3 + backward_ms - true_offset_ms` are the docstring's two equations, made concrete. Note `t3 = t2 + server_processing_ms` sits between them, untouched by offset -- processing time is server-local and does not interact with clock skew at all.

### The module docstring's closing paragraph

"Two different `(d_f, d_b)` pairs with the same sum produce the same four timestamps for a given true offset." This is the thesis, stated as a fact about the arithmetic: `offset.delay()` only ever sees `d_f + d_b`, never the individual terms, so no amount of staring at `t1..t4` can separate them.

## Failure Questions

Use the source file to answer these:

1. In `true_offset_error(forward_ms, backward_ms)`, which term -- forward or backward -- cancels when the path is symmetric, and what does "cancels" mean concretely in terms of the return value?
2. The docstring says a slower return trip "biases the reported offset downward." Using `true_offset_error()`'s formula, what sign does the error have when `backward_ms > forward_ms`, and does a positive error mean the report is too high or too low relative to truth?
3. `build_exchange()` takes `server_processing_ms` as a parameter but `true_offset_error()` does not. Why does processing time not belong in the error formula at all?
4. Two calls to `build_exchange()` use `(forward_ms=10, backward_ms=50)` and `(forward_ms=20, backward_ms=60)` with the same `true_offset_ms` and `t1`. Their `t4 - t1` (from `offset.delay()`) differ, but is there a `(forward_ms, backward_ms)` pair with a *different* sum that still produces the identical four timestamps as the first pair? What does that tell you about what `t1..t4` alone can distinguish?
5. Why is min-delay filtering (Session 04's `best_sample()`) not a fix for asymmetry, even though it correlates with "less room for the symmetry assumption to be wrong"? What would `true_offset_error()` return for a low-delay sample whose forward and backward legs still differ?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/ntp/session_03_walkthrough.py
```

The walkthrough builds a symmetric exchange (`forward_ms == backward_ms == 15`) and confirms `offset()` recovers the true offset exactly, then builds an asymmetric one (`forward_ms=10, backward_ms=50`) and confirms the report drifts by exactly `true_offset_error(10, 50) == 20.0` -- asserting the identity `reported + error == truth` directly, plus a line noting the exchange's four timestamps alone never reveal the forward/backward split that caused the drift.

## Done When

The learner can say all of the following without looking at notes:

- "The symmetry assumption is not a detail of the formula -- it is the whole reason `(t2-t1)+(t4-t3)` reduces to `2*theta` instead of something messier."
- "The error introduced by asymmetry is exactly half the gap between backward and forward delay, and the sign tells you which way the report is biased."
- "`t1` through `t4` only ever expose the sum of the one-way delays, never the two terms separately -- the protocol cannot detect the asymmetry it assumes away."

## References

- RFC 5905 Section 8 (On-Wire Protocol / clock offset and round-trip delay calculations)
