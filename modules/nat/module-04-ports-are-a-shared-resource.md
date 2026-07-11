# Session 04 / Module 04: Ports Are a Shared Resource

## Position

- Track: NAT
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/nat/module-04/index.html`
- Source file: `src/protocol_in_code/nat/ports.py`
- Walkthrough script: `examples/nat/session_04_walkthrough.py`

## Core Question

One public IP, one ephemeral port range, thousands of private hosts behind it — how does the NAT box hand out a port that no other flow is using, and what happens the moment it runs out?

## Outcome

By the end of this session, the learner should be able to:

- state the ephemeral range this toy allocates from, and why its size is the NAT's real capacity limit
- trace `allocate_port()`'s scan order, including what happens when it wraps
- explain why `release_port()` does not make a freed port immediately reusable
- name the outcome when the pool is exhausted, and what the caller receives instead of a port

## Read Order

1. Read the module comment above `EPHEMERAL_RANGE`
2. Read `AllocationOutcome`
3. Read `PortAllocator`
4. Read `allocate_port()`
5. Read `release_port()`
6. Run `examples/nat/session_04_walkthrough.py`

## Read It Like Code

```python
PortAllocator(
    public_ip,
    in_use,
    next_candidate,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `public_ip` | The pool belongs to one public address. A second public IP gets a second, independent `PortAllocator`. |
| `in_use` | Every port currently backing a live translation. Membership here is the only thing `allocate_port()` checks. |
| `next_candidate` | Where the next scan resumes. It only ever advances forward (with wraparound) — it does not rewind to a port that was just freed. |

## Decision Flow

```text
scan from next_candidate, span = EPHEMERAL_RANGE size
  candidate not in in_use  -> claim it, advance next_candidate, return the port  (ALLOCATED)
  candidate in in_use      -> try the next offset, wrapping past the top of the range back to the bottom
  every offset in the span tried and all in_use -> return None                   (POOL_EXHAUSTED)
```

## Reading Lens

The important move in this session is to stop thinking of "a free port" as something the allocator searches the whole space for, and start asking:

- where is `next_candidate` sitting right now, and does the scan reach the freed port before it wraps?
- is this pool's capacity a hard number, or does it just feel unlimited because the walkthrough never fills it?
- what does the caller get back on exhaustion — an exception, a sentinel, or something else?

## Toy Model Boundary

`~16k ports = the NAT's capacity per public IP per protocol per destination` — the docstring's framing, not this module's code. This toy allocates from one flat `EPHEMERAL_RANGE` per `PortAllocator`, with no split by protocol or by destination. Real NAT devices frequently reuse the same public port across different destinations for the same private host (port-address translation / PAT), which multiplies effective capacity far past 16k flows — that reuse dimension does not exist here. There is also no reservation of well-known or registered ports, no per-host quota, and no randomized port selection for security (RFC 6056) — the scan is a deterministic linear probe, which makes the walkthrough's wraparound scenario reproducible but is not how a hardened NAT picks ports in practice.

## Code Landmarks

### The module comment above `EPHEMERAL_RANGE`

States the capacity framing directly: the ephemeral range **is** the NAT's capacity, one port per concurrent flow per protocol per destination, until that flow's conntrack entry expires (Session 05).

### `allocate_port()`

One loop, `span` iterations at most. The modular arithmetic (`(alloc.next_candidate - low + offset) % span`) is what makes the scan wrap from `65535` back to `49152` instead of stopping at the top of the range. Returning `None` on a full scan is the only exhaustion signal — there is no exception.

### `release_port()`

The mirror of `allocate_port()`: a single `discard`. It does **not** touch `next_candidate`, which is why a just-freed port is not the next one handed out — see Failure Question 2.

## Failure Questions

Use the source file to answer these:

1. `allocate_port()` scans `range(span)` starting at `next_candidate`. If `next_candidate` is `65534` and both `65534` and `65535` are in `in_use`, what is the very next candidate the loop tries, and why?
2. A port is freed with `release_port()` immediately after `next_candidate` has advanced past it. Why does the next call to `allocate_port()` not return that freed port?
3. What does `allocate_port()` return when every port in `EPHEMERAL_RANGE` is in `in_use`, and how must a caller check for that outcome?
4. `PortAllocator.next_candidate` defaults to `EPHEMERAL_RANGE[0]`. What is the very first port `allocate_port()` returns on a freshly constructed allocator?
5. Two different `PortAllocator` instances share nothing but the same `EPHEMERAL_RANGE` constant. What has to be true about their `public_ip` fields for that to be safe?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/nat/session_04_walkthrough.py
```

The walkthrough allocates three sequential ports from an empty pool, releases the middle one and shows the next allocation skips right past the freed gap, then constructs small artificial `in_use` sets to force a near-exhausted pool, a fully exhausted pool, and a wraparound scan that finds a gap just below the top of the range before wrapping to the bottom.

## Done When

The learner can say all of the following without looking at notes:

- "The ephemeral range's size is the NAT's real capacity per public IP, per protocol, per destination — not an implementation detail."
- "allocate_port() scans forward from next_candidate and wraps once; a freed port is not reused until the scan comes back around to it."
- "Exhaustion returns None, not an exception — the caller has to check."

## References

- RFC 4787 (NAT UDP Behavioral Requirements — port allocation and preservation behavior for NAT mappings)
