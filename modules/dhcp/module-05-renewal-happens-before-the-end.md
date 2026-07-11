# Session 05 / Module 05: Renewal Happens Before the End

## Position

- Track: DHCP
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/dhcp/module-05/index.html`
- Source file: `src/protocol_in_code/dhcp/renewal.py`
- Walkthrough script: `examples/dhcp/session_05_walkthrough.py`

## Core Question

If a lease is just a dict entry that expires, why does RFC 2131 make a client start asking for a new one long before the old one runs out — and who is it even allowed to ask, at each point in that countdown?

## Outcome

By the end of this session, the learner should be able to:

- compute T1 and T2 for a given lease by hand, including the integer-floor rounding
- name all four `RenewalState` values and the exact boundary that separates each pair
- explain why RENEWING asks one specific server while REBINDING asks anyone
- explain why T1 and T2 both round down, and why that costs the client time rather than gaining it

## Read Order

1. Read the module comment above `RenewalState` (RFC 2131 §4.4.5 defaults)
2. Read `RenewalState`
3. Read `t1()`
4. Read `t2()`
5. Read `renewal_state()`
6. Read `renewal_target()`
7. Run `examples/dhcp/session_05_walkthrough.py`

## Read It Like Code

```python
renewal_state(lease, now) -> RenewalState
renewal_target(state)     -> "granting-server" | "any-server" | "none"
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `lease.granted_at` | The zero point every deadline in this module is measured from. |
| `lease.duration` | Scaled by `// 2` for T1 and `* 7 // 8` for T2 — the whole lease length matters, not just what's left. |
| `now` | Compared against T1, T2, and the lease's own expiry, in that order, to pick a `RenewalState`. |

## Decision Flow

```text
now >= granted_at + duration   -> Expired    (renewal_target: none)
now >= t2(lease)               -> Rebinding  (renewal_target: any-server)
now >= t1(lease)                -> Renewing   (renewal_target: granting-server)
otherwise                      -> Fresh      (renewal_target: none)
```

## Reading Lens

The move this session asks for is to stop treating "lease expiry" as one deadline and start reading it as three, checked in a fixed order from latest to earliest — `renewal_state()` checks expiry first, then T2, then T1, falling through to FRESH only if none of those `>=` comparisons fire. Read the `>=` in each branch specifically: at exactly T1, the state is already RENEWING, not FRESH; at exactly T2, the state is already REBINDING, not RENEWING. Nothing in this module ever uses `>`.

Ask, at every state:

- who does `renewal_target()` say to ask, and does that match what the docstring on `renewal_state()` claims — "quietly, unicast" versus "louder now, broadcast"?
- is `now` past T1 but not yet T2, or past T2 but not yet expiry — which comparison in `renewal_state()` is the one that actually fires first for this `now`?
- what does the client lose, in seconds, to the `//` floor at T1 and T2, compared to if the division were exact?

The who-do-you-ask table is the thesis of this module, and it is worth writing out explicitly because `renewal_target()`'s three-line body is easy to skim past:

| State | Boundary | Ask |
|---|---|---|
| FRESH | before T1 | none — nothing to do yet |
| RENEWING | `now >= t1(lease)`, before T2 | granting-server — quiet, unicast, the one server that already knows this lease |
| REBINDING | `now >= t2(lease)`, before expiry | any-server — loud, broadcast, because the granting server might be gone |
| EXPIRED | `now >= granted_at + duration` | none — there is nothing left to renew |

## Toy Model Boundary

Real DHCP clients can request a specific lease time via option 51, and T1/T2 can be set explicitly by the server via options 58 and 59 rather than always falling back to the RFC 2131 defaults of 50% and 87.5%. This module hard-codes those two fractions inside `t1()` and `t2()` — there is no server override path, so every lease in this course renews on the same schedule regardless of what a real server might have configured.

There is also no actual renewal *request* modeled here — Session 06's server loop only implements DORA (DISCOVER/OFFER/REQUEST/ACK), not the unicast REQUEST a real client sends at T1 to renew in place. `renewal_state()` and `renewal_target()` tell you what a client *should* do and *who* to ask; nothing in this course's source sends that message.

## Code Landmarks

### The module comment above `RenewalState`

States the two fractions from RFC 2131 §4.4.5 directly — 50% for T1, 87.5% for T2 — and flags up front that both round down, so a lease can end up "very slightly short-changed rather than ever granted extra time." That asymmetry is worth carrying into `t1()` and `t2()` before reading their bodies.

### `t1()` and `t2()`

Two one-line functions, both `granted_at + (some fraction of duration)`, both using `//`. `t2()`'s `lease.duration * 7 // 8` multiplies before dividing — read it as "seven eighths, floored," not as two separate steps that could reorder.

### `renewal_state()`'s docstring

Spells out the whole state machine in prose before the code does: FRESH does nothing, RENEWING asks quietly (unicast, the granting server), REBINDING asks loudly (broadcast, any server), EXPIRED is just over. The four-line `if` chain below it is that paragraph compiled.

### `renewal_target()`

Three lines, and the entire "who do you ask" answer for the whole module. Notice it takes a `RenewalState`, not a `Lease` or a `now` — by the time you call this, `renewal_state()` has already done all the time arithmetic.

## Failure Questions

Use the source file to answer these:

1. For a lease with `duration=100`, what integer does `t1()` return, and what integer does `t2()` return? Which operator — `//` or `/` — makes the difference between "half the lease" and the number `t1()` actually computes?
2. At `now` exactly equal to `t1(lease)`, does `renewal_state()` return FRESH or RENEWING? Which specific comparison in the function decides this, and is it `>` or `>=`?
3. At `now` exactly equal to `t2(lease)`, does `renewal_state()` return RENEWING or REBINDING? Why does the function check the T2 condition before the T1 condition rather than after?
4. What does `renewal_target()` return for `RenewalState.EXPIRED`, and what does it return for `RenewalState.FRESH` — are they the same string, and does the function distinguish those two states at all?
5. For a lease with `duration=101` (an odd number), does `t1()` round down evenly, or does the client lose a fraction of a second of "fresh" time to the floor? What is `t1()`'s return value for `granted_at=0, duration=101`?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dhcp/session_05_walkthrough.py
```

The walkthrough builds one lease, checks `RenewalState` at a point before T1, at exactly T1, at exactly T2, and at expiry, and prints `renewal_target()` for all four states as the who-do-you-ask table.

## Done When

The learner can say all of the following without looking at notes:

- "T1 is half the lease, T2 is seven-eighths, both computed with integer floor division from `granted_at`."
- "At exactly T1 the state is already RENEWING, and at exactly T2 it's already REBINDING — every boundary in this module is `>=`, never `>`."
- "RENEWING asks the one server that granted the lease; REBINDING gives up on that server and asks anyone; EXPIRED asks nobody."

## References

- RFC 2131 Section 4.4.5 (T1 and T2: default renewal at 50% of lease time, rebinding at 87.5%)
