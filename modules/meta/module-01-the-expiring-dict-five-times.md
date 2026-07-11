# Session 01 / Module 01: The Expiring Dict, Five Times

## Position

- Track: Same Shape
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/meta/module-01/index.html`
- Source file: `src/protocol_in_code/meta/expiring_state.py`
- Walkthrough script: `examples/meta/session_01_walkthrough.py`

## Core Question

Five different tracks each built "a dict keyed by identity, holding a value stamped with the time it was created, read against `now`" — so what, exactly, is left of that shape once the protocol-specific names are stripped away, and where does it break?

## Outcome

By the end of this session, the learner should be able to:

- name the four steps every expiring store in this course shares
- point to the real function in each of the five packages that performs each step
- explain why the DNS pair's before/after outcomes use `CacheOutcome`, not a re-typed string
- state the one store in this course that does not delete on expiry, and what it does instead

## Read Order

1. Read the module docstring at the top of `expiring_state.py`
2. Read `ExpiryDemo`
3. Read `demonstrate_all()` stanza by stanza — DNS, then TLS, then DHCP, then NAT, then IGMP
4. Read `common_shape()` and its docstring, including the ARP cross-reference
5. Run `examples/meta/session_01_walkthrough.py`

## Read It Like Code

```python
ExpiryDemo(
    protocol,
    what_expires,
    outcome_name,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `protocol` | Which of the five real packages produced this row — `dns`, `tls`, `dhcp`, `nat`, or `igmp`. |
| `what_expires` | The noun each package uses for its own stored value — cached answer, session ticket, address lease, conntrack entry, membership interest. Five nouns, one shape. |
| `outcome_name` | The literal `.value` of whatever real enum (or string) that package's own lookup function returned — not a paraphrase. |

## Decision Flow

```text
common_shape(), the four steps every store in demonstrate_all() takes:
  1. keyed store                                     -> a dict, keyed by the thing's identity
  2. insert stamps a time                             -> the value is frozen with its creation time
  3. read compares now against stamp+lifetime         -> arithmetic, not a background sweep, decides staleness
  4. expiry deletes (or degrades - see arp/cache.py's
     REACHABLE -> STALE, the one exception)            -> every store above forgets; ARP alone downgrades in place
```

## Reading Lens

You have now seen this dict five times. The important move in this session is to stop reading each `demonstrate_all()` stanza as five new APIs to memorize and start asking, at every stanza:

- what is the key — and is it the *whole* identity, or does using half of it (as DNS's Session 04 module warned) create a false hit?
- what did `store`/`insert`/`grant_lease`/`join`+`on_report` stamp as the creation time?
- what does the *read* function compare `now` against, and is that comparison `>=` or `>`?
- does expiry delete the entry, or — as with ARP — leave it in place but no longer trusted?

If you can answer those four questions for `dns/cache.py` from Session 04 (DNS track), `tls/resumption.py` from Session 06 (TLS track), `dhcp/leases.py` from Session 04 (DHCP track), `nat/timeout.py` from Session 05 (NAT track), and `igmp/querier.py` from Session 02 (IGMP track) without re-reading any of those five files, this session has done its job.

## Toy Model Boundary

This is a demonstration over five toy implementations, not a proof that every expiring store in the world reduces to four steps. Real caches, tickets, leases, conntrack tables, and membership trackers each carry policy this course's toy versions strip out — negative caching, ticket rotation, lease renewal races, NAT port reuse, IGMPv3's per-source state — and a production instance of any one of these five might expire on a background timer instead of at read time, unlike every toy version here. The four-step `common_shape()` is a reading aid, not a formal law; treat it as "what these five files have in common," not "what all expiring state must look like."

`now_gap` is a parameter precisely because none of these five stores read a real clock — every scenario in this session is reproducible because time is an argument, the same design choice DNS's Session 04 module called out for `lookup()`.

## Code Landmarks

### The module docstring

States the shape in one sentence before any code runs: "a dict keyed by identity, a frozen value stamped with the time it was created, and a read (or sweep) that compares `now` against `stamp + lifetime`." Everything below is that sentence, five times, in five different packages' own words.

### The NAT and IGMP stanzas' outcome strings

Unlike DNS, TLS, and DHCP — which each import a real `*Outcome` enum (`CacheOutcome`, `TicketOutcome`, `LeaseOutcome`) — the NAT and IGMP stanzas synthesize `"Hit"` / `"Expired"` strings from `nat_sweep()`'s and `expire_silent()`'s return values, because neither `nat/timeout.py` nor `igmp/querier.py` returns a typed outcome the way the cache-shaped three do. Read this as a real difference in the underlying packages' designs, not an inconsistency in this file: `nat_sweep()` and `expire_silent()` return *what expired*, a tuple of keys, and this module infers Hit/Expired from membership in that tuple.

### `common_shape()`'s docstring, the ARP cross-reference

"ARP (`arp/cache.py`) is the one exception worth cross-referencing here: a REACHABLE neighbor entry that outlives its window does not get deleted on the fourth step, it DEGRADES to STALE in place." ARP is not one of the five rows in `demonstrate_all()` — it is cited here specifically *because* it breaks step four, which is the point: the shape has four steps, and knowing the one packages that deviates is as important as knowing the four that comply.

### The DNS stanza's `assert`

`assert expired.outcome is CacheOutcome.EXPIRED` — every stanza in `demonstrate_all()` ends with an assertion against the real enum member, not the string. The row appended to `rows` uses `.value` for display, but the correctness check runs against the enum itself.

## Failure Questions

Use the source file to answer these:

1. Which row's `outcome_name` is produced by reading a real `*Outcome` enum's `.value`, and which two rows' `outcome_name` strings are synthesized by this file itself rather than returned by the underlying package? Name the two packages.
2. Why is ARP's `REACHABLE -> STALE` transition called out in `common_shape()`'s docstring instead of being added as a sixth row in `demonstrate_all()`?
3. `demonstrate_all()`'s NAT stanza calls `nat_sweep()` twice, at `now=10` and `now=30 + now_gap`. What does the *return value* of `nat_sweep()` represent, and how does that differ from what `dns_lookup()` returns?
4. Every one of the five stanzas advances the clock by a different native lifetime (30 for DNS's TTL, 3600 for TLS's ticket and DHCP's lease, 30 for NAT's UDP timeout, 260 for IGMP's membership timeout) before adding `now_gap`. Why does `now_gap` exist at all, given each stanza already knows its own lifetime?
5. Which function does the DHCP stanza call to create a lease, and which function does it call to read one back — are they the same function, the way `dns/cache.py`'s `lookup()` handles both hit and miss?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/meta/session_01_walkthrough.py
```

The walkthrough calls `demonstrate_all(now_gap=0)`, checks it returns exactly 10 rows covering all five protocols, confirms every protocol's before-row outcome differs from its after-row outcome, checks the DNS pair specifically against the real `CacheOutcome.HIT` and `CacheOutcome.EXPIRED` enum members, and confirms `common_shape()` has exactly 4 steps.

## Done When

The learner can say all of the following without looking at notes:

- "DNS caching, TLS resumption, DHCP leasing, NAT conntrack, and IGMP membership are the same four-step shape wearing five different nouns: keyed store, insert stamps a time, read compares now against stamp+lifetime, expiry deletes."
- "ARP is the one store in this course that doesn't delete on expiry — a REACHABLE entry degrades to STALE in place, and that difference is worth remembering precisely because it's the exception."
- "I can point to the real function in each of the five packages that performs each of the four steps, without re-reading the file."

## References

- `modules/dns/module-04-the-cache-answers-first.md` — DNS cache entries, the first appearance of this shape
- `modules/tls/module-06-resumption-is-a-cache-hit.md` — TLS session tickets
- `modules/dhcp/module-04-a-lease-is-a-dict-with-an-expiry.md` — DHCP address leases
- `modules/nat/module-05-state-expires-again.md` — NAT conntrack entries
- `modules/igmp/module-02-queries-keep-the-set-honest.md` — IGMP membership interest
- `modules/arp/module-01-the-cache-has-moods.md` — the ARP exception: degrade, not delete
