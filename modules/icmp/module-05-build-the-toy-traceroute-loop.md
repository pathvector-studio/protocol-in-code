# Session 05 / Module 05: Build the Toy Traceroute Loop

## Position

- Track: ICMP
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/icmp/module-05/index.html`
- Source file: `src/protocol_in_code/icmp/trace_loop.py`
- Walkthrough script: `examples/icmp/session_05_walkthrough.py`

## Core Question

If traceroute has no query that asks "where does this path go," how does looping over `ttl` and reading the wreckage assemble the answer — and what tells the loop when to stop?

## Outcome

By the end of this session, the learner should be able to:

- explain why `run_traceroute()` increments `ttl` instead of asking any router directly
- trace what `ToyTracer.trace` records on a silent hop versus a hop that answers
- state exactly which condition ends the loop, and why it is not simply "ttl reached max_ttl"
- run `run_traceroute()` over a path with a silent hop and read the resulting tuple correctly

## Read Order

1. Read the module docstring above `run_traceroute()`
2. Read `ToyTracer`
3. Read `run_traceroute()`'s signature and the `for ttl in range(...)` loop
4. Read the `result.answerer is None` branch
5. Read the `IcmpType.TIME_EXCEEDED` vs. else branch, and the `break`
6. Read `demo_path_with_silent_hop()`
7. Run `examples/icmp/session_05_walkthrough.py`

## Read It Like Code

```python
run_traceroute(
    tracer,
    path,
    max_ttl=DEFAULT_MAX_TTL,
)
```

## Parts List

Every name `trace_loop.py` imports was taught by an earlier session in this track. The capstone's only new code is the loop that drives them.

| Import | Session that taught it | What it contributes to `run_traceroute()` |
|---|---|---|
| `message.IcmpType` | 01 | The type check (`TIME_EXCEEDED` vs. everything else) that decides whether the loop continues or `break`s. |
| `unreachable.UnreachableCode` | 02 | `PORT_UNREACHABLE.value`, used only to format the trace line when the destination answers — the loop itself does not branch on the code, only on `icmp_type`. |
| `ttl.HopOutcome`, `decrement_and_decide`, `expire` | 03 | Used inside `probing.probe()`, one layer down — `trace_loop.py` never calls `ttl.py` directly, it inherits the hop-budget arithmetic through `probe()`. |
| `probing.Hop`, `Path`, `probe` | 04 | `probe()` is called once per `ttl` inside the loop; `Hop` and `Path` build the `demo_path_with_silent_hop()` fixture. |

## Decision Flow

```text
run_traceroute(tracer, path, max_ttl):
  for ttl in 1 .. max_ttl:
    result = probe(path, ttl, dst_port=33434)

    result.answerer is None
      -> append "*" to answerers, log "ttl=N -> * (no response)", continue

    result.message.icmp_type is TIME_EXCEEDED
      -> append result.answerer, log "ttl=N -> <answerer> TimeExceeded", continue

    otherwise (PORT_UNREACHABLE from the destination)
      -> append result.answerer, log "ttl=N -> <answerer> Port Unreachable", break

  return tuple(answerers)
```

## Reading Lens

The important move in this session is to stop reading `run_traceroute()` as "ping every hop" and start asking:

- at this `ttl`, did `probe()` return silence, a diagnosis from a router, or a confession from the destination — and which of those three is the only one that stops the loop?
- what does `tracer.trace` say happened, in order, and would that log alone tell a debugger which hops answered and which didn't?
- how many entries are in the returned tuple compared to `max_ttl` — did the loop stop early, and why?

## Toy Model Boundary

Real traceroute sends three probes per `ttl` and reports round-trip time for each, so a single flaky reply doesn't look like a dead hop; this toy sends exactly one probe per `ttl` and records no timing at all. Real paths can wobble under ECMP load balancing — three probes at the same `ttl` legitimately naming three different routers is the classic real-world confusion traceroute users run into — and this toy sidesteps it entirely because `Path` is a fixed tuple of hops with no per-probe routing variance. `run_traceroute()` also has no retry: a silent hop is recorded once as `"*"` and the loop moves straight to the next `ttl`, where a real traceroute implementation would typically still send three probes before giving up on that hop.

## Code Landmarks

### The module docstring above `run_traceroute()`

"Traceroute never asks anyone where the path goes — it makes every router confess by sending doomed packets." This is the whole track's thesis in one line, restated for the loop rather than the single probe.

### `result.answerer is None`

The only branch that does not append a real name to `answerers`. `SILENT_MARKER` (`"*"`) fills the gap so the returned tuple keeps one entry per `ttl` attempted, silent hops included.

### The `IcmpType.TIME_EXCEEDED` check

This is the *only* thing that decides whether the loop keeps going or stops — not `ttl` reaching `max_ttl`, not the destination's IP address being known in advance. Any reply whose `icmp_type` is not `TIME_EXCEEDED` is treated as the destination's `PORT_UNREACHABLE` and ends the loop with `break`.

### `demo_path_with_silent_hop()`

"Three hops, the middle one configured not to answer — a common real-world firewall behavior." The fixture exists specifically to exercise the `SILENT_MARKER` branch in the walkthrough, not just the happy path.

## Failure Questions

Use the source file to answer these:

1. `run_traceroute()` breaks out of its loop on exactly one condition. What is it, expressed in terms of `result.message.icmp_type` — not in terms of `ttl` or `max_ttl`?
2. If every hop in `path.hops` has `responds=False`, what does `run_traceroute()` return when it finally reaches the destination at `ttl == len(path.hops) + 1`? Does the destination's silence work the same way a `Hop`'s silence does?
3. What is the difference between what `tracer.trace` records for a silent hop and what it records for a hop that answers `TIME_EXCEEDED`? Which one advances `answerers` with a real name?
4. If `max_ttl` is reached without any probe returning `PORT_UNREACHABLE`, how many entries does the returned tuple have, and does the loop ever call `probe()` with `ttl > max_ttl`?
5. `run_traceroute()` calls `probe(path, ttl, dst_port=33434)` with a hardcoded port on every iteration. What would have to change about the loop, not about `probe()`, for two different traceroute runs to use two different `dst_port` values?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/icmp/session_05_walkthrough.py
```

The walkthrough runs `run_traceroute()` over `demo_path_with_silent_hop()` and checks the returned tuple is exactly `('r1', '*', 'r3', '10.0.0.99')`, checks `tracer.trace` contains the `ttl=2` silence line, checks the loop stopped at `PORT_UNREACHABLE` well short of `max_ttl` (hop count `< DEFAULT_MAX_TTL`), checks the last trace line names the destination's `Port Unreachable`, and finally runs a fully-responsive two-hop path to confirm no `"*"` appears when every hop answers.

## Done When

The learner can say all of the following without looking at notes:

- "The loop increments `ttl` and calls `probe()` once per value — it never asks any router for the path directly."
- "A silent hop logs `*` and the loop continues; only a `PORT_UNREACHABLE` from the destination logs the final line and breaks."
- "Every name in `trace_loop.py` — the message types, the unreachable code, the ttl arithmetic, the probe itself — was taught by an earlier session; this module is the wiring, not new protocol logic."

## References

- RFC 792 (Internet Control Message Protocol)
- The traceroute technique itself is attributed to Van Jacobson's `traceroute` utility — no RFC governs the trick of using deliberately doomed, incrementing-ttl packets to enumerate a path. RFC 792 defines the ICMP messages the technique exploits; it does not define traceroute.
