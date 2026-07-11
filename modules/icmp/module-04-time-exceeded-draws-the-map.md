# Session 04 / Module 04: Time Exceeded Draws the Map

## Position

- Track: ICMP
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/icmp/module-04/index.html`
- Source file: `src/protocol_in_code/icmp/probing.py`
- Walkthrough script: `examples/icmp/session_04_walkthrough.py`

## Core Question

What decides which router answers a probe, and why is an "error" reply the probe's success signal instead of its failure?

## Outcome

By the end of this session, the learner should be able to:

- explain how `ttl` and a path's hops together decide who answers a given probe
- describe what happens when the hop that should answer is configured silent
- explain why a probe that outlives the whole path gets answered by the destination, not by an error condition
- state why UDP traceroute deliberately targets a high, unused port

## Read Order

1. Read `Hop` and `Path`
2. Read `ProbeResult`
3. Read `_quote_for()`
4. Read `probe()`'s docstring
5. Read `probe()`'s body
6. Run `examples/icmp/session_04_walkthrough.py`

## Read It Like Code

```python
ProbeResult(
    answerer,
    message,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `answerer` | `str \| None` — the name of whoever replied, or `None` if nobody did. This is the field every caller checks first. |
| `message` | `IcmpMessage \| None` — the actual reply, when there is one. `None` exactly when `answerer` is `None`. |

## Decision Flow

```text
walk path.hops, decrementing ttl once per hop (via ttl.decrement_and_decide)

ttl reaches 0 at hop i, hop i.responds is True   -> hop i answers TIME_EXCEEDED
ttl reaches 0 at hop i, hop i.responds is False  -> silence: ProbeResult(None, None)
ttl outlasts every hop in path.hops              -> path.destination answers PORT_UNREACHABLE
```

## Reading Lens

The important move in this session is to stop reading `probe()` as "send a packet, get an error back" and start asking:

- at this `ttl`, which hop index runs out of budget — and does that hop actually reply?
- is the reply in front of me a diagnosis from someone along the way, or a confession from the destination itself?
- what port did the quoted packet inside the reply carry, and does it match what the probe sent?

## Toy Model Boundary

Real traceroute sends three probes per ttl and reports round-trip time for each; this toy sends exactly one probe per ttl and reports no timing at all — there is no clock in `probe()`. Real paths can wobble hop-to-hop under ECMP load balancing, so three probes at the same ttl can legitimately name three different routers; this toy's `Path` is a fixed tuple of hops, so the same `ttl` always produces the same answerer. That wobble is the classic real-world traceroute confusion — asymmetric or ECMP-balanced hops making one "hop" look like it has multiple routers — and this toy sidesteps it entirely by construction.

## Code Landmarks

### `probe()`'s docstring

"Time exceeded draws the map: send a doomed packet, see who confesses to killing it." The docstring names the whole session's thesis outright: the destination's complaint is the probe's success.

### The `for hop in path.hops` loop

One `decrement_and_decide` call per hop, imported from Session 03. `probe()` does not reimplement ttl arithmetic — it reuses the hop-budget decision and only adds what happens next: who gets to answer.

### The `not hop.responds` branch

A silent hop is not an error case in this code — it is a normal, modeled outcome. `ProbeResult(answerer=None, message=None)` is a first-class return value, not an exception.

### The fall-through after the loop

If the `for` loop finishes without any hop reaching `HopOutcome.EXPIRED`, control falls past it entirely — this is `ttl` outlasting the whole path, and the only place `path.destination` (not a `Hop`) becomes the answerer.

### `_quote_for()`

Every reply, whether from a hop or the destination, quotes the same `dst_port` the caller passed to `probe()`. That quoted port is what lets a real traceroute tool match the reply back to the probe that caused it.

## Failure Questions

Use the source file to answer these:

1. `probe(path, ttl=2, dst_port=33434)` is called against a path whose second hop has `responds=False`. What does `probe()` return, and what would change if that hop instead had `responds=True`?
2. What has to be true about `ttl` relative to `len(path.hops)` for `path.destination` — rather than any `Hop` — to be the one that answers?
3. Two calls to `probe()` use the same `path` and `ttl` but different `dst_port` values. Do they produce the same `answerer`? Do they produce the same `message`?
4. `probe()` calls `ttl.decrement_and_decide()` once per hop inside its loop. What field of that function's return value does `probe()` actually branch on to decide `HopOutcome.EXPIRED`?
5. If `path.hops` is empty, what does `probe()` return for any `ttl >= 1`? Which branch of the function handles this?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/icmp/session_04_walkthrough.py
```

The walkthrough builds a three-hop path with a silent middle hop, then probes it at increasing `ttl`: the first hop confesses at `ttl=1`, the silent hop returns nothing at `ttl=2`, the third hop confesses at `ttl=3`, and any `ttl` past the path's length gets answered by the destination with `PORT_UNREACHABLE` — the error that is actually the probe's success. It also checks that the quoted packet inside that final reply still names the original `dst_port`.

## Done When

The learner can say all of the following without looking at notes:

- "The hop where `ttl` hits zero is the one forced to answer — unless it's configured silent, in which case nothing comes back at all."
- "A probe that outlives the whole path is answered by the destination, not by a router along the way — and that answer is `PORT_UNREACHABLE`, not a mistake."
- "The destination's complaint about an unreachable port is the probe's success signal, not its failure."

## References

- RFC 792 (Internet Control Message Protocol)
- The traceroute technique itself is attributed to Van Jacobson's `traceroute` utility — no RFC governs the trick of using deliberately doomed, incrementing-ttl packets to enumerate a path. RFC 792 defines the ICMP messages the technique exploits; it does not define traceroute.
