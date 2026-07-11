# Session 01 / Module 01: The Highest Priority Speaks

## Position

- Track: HA (VRRP+BFD)
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/ha/module-01/index.html`
- Source file: `src/protocol_in_code/ha/vrrp_election.py`
- Walkthrough script: `examples/ha/session_01_walkthrough.py`

## Core Question

If several routers share one virtual IP, how does the code decide which one gets to be master?

## Outcome

By the end of this session, the learner should be able to:

- explain why priority 255 is not just "high priority" but a different category of claim
- name the exact tuple `elect()` compares candidates on, in order
- state RFC 5798's tiebreak rule and why it is guaranteed to produce exactly one winner
- explain the difference between "the best router" and "the router that currently masters," and why `should_preempt()` exists to bridge that gap

## Read Order

1. Read the module docstring at the top of the file
2. Read `PRIORITY_OWNER`
3. Read `_ip_key()`
4. Read `VrrpRouter`
5. Read `elect()`
6. Read `should_preempt()`
7. Run `examples/ha/session_01_walkthrough.py`

## Read It Like Code

```python
VrrpRouter(
    name,
    priority,
    primary_ip,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `priority` | The primary ranking key. 1-254 is configured; 255 is reserved and means something categorically different. |
| `primary_ip` | The tiebreak key. Every router in a group has a distinct one, so it always resolves a tie. |
| `name` | Identity only — never part of the comparison. |

## Decision Flow

```text
elect(routers):
  compare every router on (priority, ip_key(primary_ip))
  return the max

should_preempt(current_master, candidate, preempt_enabled):
  preempt_enabled is False        -> False   (never take over)
  candidate.priority not > current -> False   (not actually better)
  otherwise                       -> True    (better candidate, preemption allowed)
```

## Reading Lens

The important move in this session is to stop reading `elect()` as VRRP-specific and start asking:

- what is the comparison key, and is it a single value or a tuple?
- what happens when two candidates tie on the first element of that tuple?
- is the max being taken over all candidates at once, or incrementally as they're heard from?

This is the third time this course elects-by-comparison: OSPF's `dr_election.py` ranks candidates on `(priority, router_id)`, RIP's `route.py` `better()` ranks on a single metric, and VRRP here ranks on `(priority, primary_ip)`. Same shape — rank every candidate on a comparison key and take the max — a different, protocol-specific rulebook filling in what the key actually is. Once you've read one, the other two are the same function with different tuples.

## Toy Model Boundary

Real VRRP maps the elected master onto a virtual MAC address and answers ARP for the virtual IP; a backup that becomes master has to send a gratuitous ARP so the LAN's forwarding tables catch up. None of that exists here — this module stops at "who wins the comparison," not "how the network finds out." `elect()` also assumes it is handed the full candidate set at once; the real protocol assembles that set advertisement by advertisement, which is Session 02's job.

## Code Landmarks

### `PRIORITY_OWNER`'s docstring

"It is not 'high priority,' it is authoritative." The address owner isn't merely favored by the comparison — RFC 5798 reserves 255 so that a router configured with the virtual IP as its own real address always wins, by construction. `elect()` doesn't special-case this; the ordinary `max()` on the tuple handles it because nothing else can reach 255.

### `_ip_key()`

Turns `"192.0.2.10"` into `(192, 0, 2, 10)` — a tuple of ints, not a string. Comparing IP strings lexically would rank `"192.0.2.9"` above `"192.0.2.10"`; comparing the parsed tuple ranks them numerically, the way the RFC intends.

### `elect()`'s one line

`max(routers, key=lambda router: (router.priority, _ip_key(router.primary_ip)))`. Reading this line is the whole session: Python's tuple comparison already does the "compare priority first, break ties by IP" work — the function doesn't need an `if` for the tiebreak at all.

### `should_preempt()`'s docstring

Both sentences on the tradeoff (preemption on: fast, predictable failback; preemption off: less churn on flaky links) are equally valid engineering choices in the source — this module resists picking a side, and the walkthrough exercises both.

## Failure Questions

Use the source file to answer these:

1. Two routers are configured with the same priority. What is the exact second element of the comparison tuple that decides between them, and why does `_ip_key()` exist instead of comparing `primary_ip` strings directly?
2. A router configured with `priority=255` and a router configured with `priority=254` are both candidates. Can the `priority=254` router ever win `elect()` against it? Why not, structurally?
3. `should_preempt()` is called with a `candidate` whose priority is lower than `current_master`'s, and `preempt_enabled=True`. What does it return, and which line decides that regardless of the flag?
4. If `preempt_enabled=False`, does `should_preempt()` ever look at the two routers' priorities at all? Which line makes that comparison unreachable?
5. `elect()` takes a `tuple[VrrpRouter, ...]` and returns a single `VrrpRouter`. What would happen if it were called with an empty tuple — is that guarded anywhere in this file?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/ha/session_01_walkthrough.py
```

The walkthrough elects among an address owner and two configured priorities, breaks a tie by primary IP in both tuple orders, and flips `should_preempt()`'s answer by toggling `preempt_enabled` and by lowering the candidate's priority.

## Done When

The learner can say all of the following without looking at notes:

- "Priority 255 isn't the top of the range — it's a reserved category for the address owner, and nothing else can reach it."
- "elect() is one max() call over a (priority, ip) tuple; the tiebreak is built into how tuples compare, not a separate if."
- "should_preempt() answers a policy question, not a correctness question — the RFC doesn't mandate which way you set the flag."

## References

- RFC 5798 Section 1.2 (VRRP overview, priority and preemption)
- RFC 5798 Section 4.1 (Master election, address owner priority 255)
