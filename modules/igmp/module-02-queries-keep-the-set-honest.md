# Session 02 / Module 02: Queries Keep the Set Honest

## Position

- Track: IGMP
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/igmp/module-02/index.html`
- Source file: `src/protocol_in_code/igmp/querier.py`
- Walkthrough script: `examples/igmp/session_02_walkthrough.py`

## Core Question

Nothing in `membership.py` ever forgets a host on its own — so what makes a `GroupTable` trustworthy after a host crashes, unplugs, or roams off-link without ever calling `leave()`?

## Outcome

By the end of this session, the learner should be able to:

- explain why `GroupTable` alone cannot detect a host that silently disappeared
- name the two RFC 2236 timers this module models and what each one is for
- trace `expire_silent()`'s boundary comparison and say, at exactly the timeout, whether a host is still a member
- recognize this module as the third appearance of the expiring-dict shape, and name the other two by file

## Read Order

1. Read the module comment above `QUERY_INTERVAL`
2. Read `QUERY_INTERVAL` and `MEMBERSHIP_TIMEOUT`
3. Read `MembershipState`
4. Read `on_report()`
5. Read `expire_silent()`
6. Read `report_suppression()`
7. Run `examples/igmp/session_02_walkthrough.py`

## Read It Like Code

```python
MembershipState(
    last_report_at,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `last_report_at` | `dict[tuple[str, str], int]` keyed by `(group, host)` — the clock time of the most recent report for that pair. There is no other state; "is this host still here" is entirely a function of this one timestamp. |

## Decision Flow

```text
on_report(group, host, now)
  -> last_report_at[(group, host)] = now        (always overwrites; no other branch)

expire_silent(state, table, now), per (group, host) pair:
  now - last_seen >= MEMBERSHIP_TIMEOUT   -> expired: drop from last_report_at, leave(table, group, host)
  otherwise                               -> untouched, still a member
```

## Reading Lens

This is the expiring-state shape's third appearance in this course, and the module comment above `QUERY_INTERVAL` says so directly:

- **DNS, Session 04** (`src/protocol_in_code/dns/cache.py`) — a `CacheEntry` stamped with `stored_at`, expiring against `ttl`, checked inside `lookup()`.
- **DHCP, Session 04** (`src/protocol_in_code/dhcp/leases.py`) — a `Lease` stamped with `granted_at`, expiring against `duration`, checked inside `lookup_lease()`.
- **IGMP, Session 02** (here) — a `(group, host)` pair stamped with `last_report_at`, expiring against `MEMBERSHIP_TIMEOUT`, checked inside `expire_silent()`.

What varies this time is *where* the check runs. DNS and DHCP check expiry lazily, inside the read path — `lookup()` and `lookup_lease()` are also the only place staleness is ever discovered. IGMP checks it eagerly, on a schedule: `expire_silent()` runs once per query cycle, not once per read, because — as the docstring puts it — "nothing here is 'read' the way a cache entry is." What expires is not a cached answer or a granted address; it's interest itself. A host that stops answering queries is, for forwarding purposes, no longer there, even though nothing it did was an explicit `leave()`.

Ask, at every line:

- what pair is this timestamp keyed by, and when was it last written?
- is this expiry check happening because someone asked (lazy), or because a cycle ran (eager)?
- did `expire_silent()` just call `leave()` on `table` — and would `membership.py`'s key-deletion behavior from Session 01 now apply?

## Toy Model Boundary

`QUERY_INTERVAL = 125` and `MEMBERSHIP_TIMEOUT = 260` are named constants, not derived from a robustness variable or a configurable max-response-time the way real IGMPv2 timers are (RFC 2236 computes the group membership interval from the query interval and the max response time, not as a bare literal). There is no last-member query, no leave-latency reduction, and no query retransmission — a host that leaves takes the full timeout to be noticed, with no fast path. `report_suppression()` always picks the first name in the tuple it's handed; there is no random suppression timer, and no reduced-timer-on-hearing-another-report simulation — just "one response is enough" modeled as a single deterministic choice.

## Code Landmarks

### The module comment above `QUERY_INTERVAL`

Names this as the expiring-state family's third member and states the theme in one sentence: "here what expires is stale INTEREST." Read it before anything else in the file — it is the thesis for the whole session.

### `on_report()`

One line, no branches: the timestamp is always overwritten, whether this is the first report ever seen for the pair or the hundredth. There is no "already reported this cycle" special case.

### `expire_silent()`

The landmark comparison is `now - last_seen >= MEMBERSHIP_TIMEOUT`. It is `>=`, not `>` — a host silent for *exactly* `MEMBERSHIP_TIMEOUT` seconds is expired on this call, not on the next one. The docstring calls this out explicitly as the timeout side of the same shape as `ResolverCache.lookup` and `LeaseTable.lookup_lease`.

### `report_suppression()`

The docstring's mechanism explanation is the landmark: reports are multicast to the group address, so every other member overhears the first answer and cancels its own timer. The function models "pick the first responder" and the saving is `len(group_members_who_heard) - 1` messages versus a naive every-member-answers design.

## Failure Questions

Use the source file to answer these:

1. At exactly `now - last_seen == MEMBERSHIP_TIMEOUT`, does `expire_silent()` treat the pair as expired or still a member? Which comparison operator in the source decides this, and what would change if it were `>` instead?
2. `expire_silent()` calls `leave(table, group, host)` for each expired pair. If that pair was the group's last member, what does `table.groups` look like immediately afterward, and which Session 01 function is responsible for that?
3. `on_report()` is called for a `(group, host)` pair that has never been seen before. Does it raise, or does it behave the same as an update to an existing pair? Where in the source is that guaranteed?
4. `report_suppression()` is called with an empty tuple. What does the source do, and what does that tell you about who is responsible for checking "did anyone report" before calling it?
5. The module comment names two other files that expire stale state the same way. Name both file paths and, for each, what field plays the role `last_report_at` plays here.

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/igmp/session_02_walkthrough.py
```

The walkthrough reports a host, checks it survives one tick before `MEMBERSHIP_TIMEOUT` and is gone exactly at the timeout, shows a re-reported host surviving past where the first host expired, and exercises `report_suppression()` on both a two-member group and an empty tuple.

## Done When

The learner can say all of the following without looking at notes:

- "`GroupTable` never forgets a host on its own — `querier.py` is the only thing that tests whether a member is still really there."
- "`expire_silent()` expires a pair at exactly `now - last_seen == MEMBERSHIP_TIMEOUT`, not one tick later."
- "This is the expiring-dict shape's third appearance — DNS's cache, DHCP's leases, and now IGMP's interest — but here the check runs on a query cycle, not at read time."

## References

- RFC 2236 Section 1 (Introduction — the querier's role in testing membership over time)
- RFC 2236 Section 3 (message formats and the timers this module names: query interval, max response time)
- RFC 2236 Section 6 (host state diagram — report suppression on hearing another member's report)
