# Session 03 / Module 03: Candidates Are Gathered, Not Chosen

## Position

- Track: ICE
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/ice/module-03/index.html`
- Source file: `src/protocol_in_code/ice/candidates.py`
- Walkthrough script: `examples/ice/session_03_walkthrough.py`

## Core Question

Which addresses become candidates, and what decides the order a peer should try them in — and how are those two questions kept completely separate?

## Outcome

By the end of this session, the learner should be able to:

- list the three `CandidateType` values and what each means about how the address was learned
- explain `gather()`'s three independent conditions for adding a host, reflexive, or relayed candidate
- explain why a STUN response that matches the local address does not produce a reflexive candidate
- compute `candidate_priority()` by hand for two candidates and explain why type dominates the ordering

## Read Order

1. Read the module comment at the top of the file
2. Read `CandidateType`
3. Read `TYPE_PREFERENCE`
4. Read `Candidate`
5. Read `candidate_priority()`
6. Read `gather()`
7. Run `examples/ice/session_03_walkthrough.py`

## Read It Like Code

```python
Candidate(
    ctype,
    ip,
    port,
    base_ip,
    base_port,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `ctype` | One of `HOST`, `SERVER_REFLEXIVE`, `RELAYED` — how the address was learned, which is the entire input to `TYPE_PREFERENCE`. |
| `ip` / `port` | The address this candidate is actually reachable at. |
| `base_ip` / `base_port` | The local socket this candidate was derived from — every candidate `gather()` produces here traces back to the same base. |

## Decision Flow

```text
host candidate         -> always gathered (it's just the local socket)
reflexive candidate    -> gathered only if stun_response is not None AND (mapped_ip, mapped_port) != local_addr
relayed candidate      -> gathered only if turn_addr is not None
```

## Reading Lens

The important move in this session is to stop thinking of candidate gathering as a filtering or ranking step and start asking:

- for each candidate type, what is the one condition that has to be true for it to appear at all?
- does `gather()` ever compare candidates to each other, or only decide, one type at a time, whether that type exists?
- where does ordering enter the picture — inside `gather()`, or entirely in a separate function?

## Toy Model Boundary

Real ICE candidate gathering (RFC 8445 SS5.1.1) also includes peer-reflexive candidates discovered during connectivity checks themselves, mDNS-obscured host candidates for privacy, and separate gathering passes per IP family when a host is dual-stack (IPv4 and IPv6 candidates gathered and prioritized together). This module keeps to the three candidate types whose existence can be decided from data already in hand — a local address, an optional STUN response, an optional TURN allocation — so the enumerate-then-prioritize structure stays the whole story.

## Code Landmarks

### Module comment

States the thesis directly: every address a host might be reachable at becomes a `Candidate` first, and only later does anything decide which of them actually works. This module is pure enumeration plus one sorting formula — nothing here picks a winner.

### `TYPE_PREFERENCE`

RFC 8445 SS5.1.2.2's recommended values: `HOST` 126, `SERVER_REFLEXIVE` 100, `RELAYED` 0. The comment explains the ordering: a direct route is cheaper than one that needs a STUN-visible mapping, and a relay costs a third party bandwidth, so it is the last resort.

### `candidate_priority()`

One line, the literal RFC 8445 SS5.1.2.1 formula: `(2**24) * TYPE_PREFERENCE[ctype] + (2**8) * local_pref + (256 - component_id)`. The `2**24` multiplier on type preference means type dominates the result — no `local_pref` value can make a `RELAYED` candidate outrank a `HOST` candidate, because even the smallest possible gap between adjacent type preferences (26, between 126 and 100, or 100, between 100 and 0) times `2**24` dwarfs anything `local_pref`'s `2**8` term can contribute.

### `gather()`

The main reading target. Three independent conditions, one per candidate type, each appended in order: host is unconditional; reflexive requires both that `stun_response is not None` and that the mapped address actually differs from `local_addr` — if a STUN query happens to report back exactly the local address (no NAT in the path, or a NAT that happens not to rewrite anything observable), reflexive is skipped as a duplicate, not gathered and then discarded; relayed requires `turn_addr is not None`, and `gather()` never allocates a TURN address itself — it only records that an allocation already exists.

## Failure Questions

Use the source file to answer these:

1. What are the two separate conditions `gather()` checks before appending a `SERVER_REFLEXIVE` candidate? Why are both needed?
2. If `stun_response` is not `None` but its `(mapped_ip, mapped_port)` equals `local_addr`, does `gather()` add a reflexive candidate? What line decides this?
3. Does `gather()` ever call anything that allocates a TURN address? What does `turn_addr is not None` actually represent?
4. Given `candidate_priority(CandidateType.RELAYED, local_pref=65535)` and `candidate_priority(CandidateType.SERVER_REFLEXIVE, local_pref=0)`, which is larger? Work it out from `TYPE_PREFERENCE` and the formula's multipliers.
5. What field do every candidate `gather()` produces from one call share, regardless of `ctype`? What does that tell you about where "base" fits in ICE's model of a candidate?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/ice/session_03_walkthrough.py
```

The walkthrough calls `gather()` with no STUN and no TURN (host only), with a STUN response that differs from local (host plus reflexive), with a STUN response identical to local (reflexive is asserted absent), with a TURN allocation (host plus relayed), and with everything present (all three) — then computes `candidate_priority()` for all three types at the same `local_pref` and asserts the ordering HOST > REFLEXIVE > RELAYED with the actual numbers printed.

## Done When

The learner can say all of the following without looking at notes:

- "Gathering asks one independent question per candidate type — it never compares candidates to decide whether to include them."
- "A STUN response that matches the local address produces no reflexive candidate, because reflexive exists to report something new, not to duplicate host."
- "Priority is dominated by type preference; `local_pref` can only rank candidates within the same type, never across types."

## References

- RFC 8445, Section 5.1 (gathering candidates, including SS5.1.1 candidate types and SS5.1.2 priorities)
