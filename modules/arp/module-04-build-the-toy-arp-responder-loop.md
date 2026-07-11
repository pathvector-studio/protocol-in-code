# Session 04 / Module 04: Build the Toy ARP Responder Loop

## Position

- Track: ARP/ND
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/arp/module-04/index.html`
- Source file: `src/protocol_in_code/arp/responder_loop.py`
- Walkthrough script: `examples/arp/session_04_walkthrough.py`

## Core Question

What does one host's whole ARP life look like — sending, queuing, answering, and gleaning — when it's wired into a single object instead of three separate demos?

## Outcome

By the end of this session, the learner should be able to:

- name every field on `ToyArpNode` and which earlier session's module owns the behavior behind it
- trace `send_to()`'s branch and say which two states deliver immediately versus which trigger a queue-and-ask
- explain what "gleaning" means in `on_request()`, and why it happens before the function even checks whether the request is for our own IP
- run `run_resolution()` for two nodes end to end and read both traces to confirm what happened on each side

## Read Order

1. Read `ToyArpNode`'s field list top to bottom
2. Read `tick()`
3. Read `send_to()`
4. Read `on_request()`
5. Read `on_reply()`
6. Read `run_resolution()`
7. Run `examples/arp/session_04_walkthrough.py`

## Read It Like Code

```python
ToyArpNode(
    name,
    my_ip,
    my_mac,
    cache,
    pending,
    clock,
    trace,
)
```

## Parts List

Every field and every function `responder_loop.py` imports was taught by an earlier session in this track. The capstone's only new code is the wiring between them — the whole file is deliberately compact, about seventy lines, because the track itself is small: three focused modules feeding one loop.

| Import | Session that taught it | What it contributes to `ToyArpNode` |
|---|---|---|
| `NeighborCache`, `NeighborState`, `confirm`, `lookup`, `start_resolution` | 01 | `cache`; `lookup()` drives `send_to()`'s REACHABLE/STALE-vs-else branch; `confirm()` is what `on_request()`'s glean and `on_reply()`'s confirmation both call. |
| `ArpAnnouncement` | 03 | The return type of `on_request()` and the argument type of `on_reply()` — the announcement object that carries an `is-at` reply between two nodes. |
| `PendingQueue`, `enqueue`, `flush` | 02 | `pending`; `send_to()` calls `enqueue()` when a mapping isn't usable yet, and `on_reply()` calls `flush()` once a reply confirms the mapping. |

Session 03's `gratuitous.py` also defines `process_announcement()` and `AcceptPolicy`, but `responder_loop.py` does not import either — this capstone's `on_request()`/`on_reply()` pair implements its own trust logic (always confirm on reply, always glean on request) rather than routing through Session 03's policy switch. That is a deliberate simplification, not an oversight — see Toy Model Boundary.

## Decision Flow

```text
send_to(ip, packet_label):
  lookup(cache, ip, clock)
    state is REACHABLE or STALE -> trace "send ... via <mac> (<state>)", return mac
    state is None                -> start_resolution(cache, ip, clock)
    (state is None or INCOMPLETE) -> enqueue(pending, ip, packet_label), trace "queue ... who-has", return None

on_request(ip_asked, from_ip, from_mac):
  confirm(cache, from_ip, from_mac, clock)      -- glean runs first, unconditionally
  trace "glean <from_ip> -> <from_mac> from the request"
  ip_asked != my_ip -> return None               -- not asking about me, stop here
  otherwise         -> trace "is-at <my_mac> for <ip_asked>", return ArpAnnouncement(..., is_reply_to_us=True)

on_reply(announcement):
  confirm(cache, announcement.ip, announcement.mac, clock)
  delivered = flush(pending, announcement.ip)
  trace "confirmed ... delivering <delivered>"
  return delivered

run_resolution(a, b, packet_label):
  mac = a.send_to(b.my_ip, packet_label)
  mac is not None -> return (packet_label,)        -- already resolved, delivered immediately
  announcement = b.on_request(ip_asked=b.my_ip, from_ip=a.my_ip, from_mac=a.my_mac)
  announcement is None -> return ()                 -- b wasn't asked about itself (can't happen in this call shape)
  return a.on_reply(announcement)
```

## Reading Lens

The important move in this session is to stop reading `cache.py`, `pending.py`, and `gratuitous.py` in isolation and start asking, at every line of `responder_loop.py`:

- which of the imported names is doing the actual work on this line, and which session taught it?
- is this call reading the cache (`lookup()`) or writing it (`confirm()`, `start_resolution()`)?
- what changed in `self.trace` as a result of this call, and would that line alone tell a debugger what happened on this node?

Pay particular attention to `on_request()`'s ordering: the glean — `confirm(cache, from_ip, from_mac, self.clock)` — runs and is traced *before* the function even checks `if ip_asked != self.my_ip`. That means every node that receives a who-has request learns the asker's mapping, whether or not the request was actually about this node's own IP. This is real ARP behavior, not a toy shortcut: a host can populate its neighbor cache just from overhearing a request addressed to someone else's IP, as long as the request names this host as the source. It is also the direct capstone payoff of Session 03's warning — gleaning happens with no authentication check at all, the same trust-on-arrival shape that made `ACCEPT_ALL` a spoofing surface.

## Toy Model Boundary

`send_to()` never retries or times out an `INCOMPLETE` resolution — if no reply ever arrives, the packets queued behind that IP sit in `pending` forever, since nothing in this file calls `drop_all()`. There is exactly one broadcast-shaped operation implied here (`who-has`) and it is represented purely as a trace line, not a real frame — `on_request()` is called directly by `run_resolution()`, not discovered via any broadcast domain or interface model. `on_request()` and `on_reply()` always trust what they're given — Session 03's `AcceptPolicy` and `process_announcement()` are not wired into this loop at all, so this capstone's nodes behave like `gratuitous.py`'s `ACCEPT_ALL` policy by construction, with no `ONLY_IF_KNOWN` option available. `run_resolution()` only demonstrates the two-node, single-packet-label resolution shape; it does not drive multiple concurrent resolutions or show what happens when `on_request()` is called for an IP that isn't the responder's own (the `announcement is None` branch is reachable in principle but `run_resolution()`'s own call shape never triggers it, since it always asks `b` about `b.my_ip`).

## Code Landmarks

### `ToyArpNode`'s field list

`cache` and `pending` are each their own dataclass from Sessions 01 and 02, constructed fresh per node via `field(default_factory=...)`. `trace` is a plain list of strings — the same "read the trace as the source of truth" idea as the TCP track's capstone.

### `send_to()`

The main reading target for the resolved-vs-unresolved fork. Notice `if result.state is None: start_resolution(...)` only fires for a *brand-new* IP — if the state is already `INCOMPLETE` (a resolution already in flight), `start_resolution()` is skipped and the packet just joins the existing queue via `enqueue()`.

### `on_request()`

Read this function for the ordering, not just the logic. The glean-then-answer sequence is the whole point: gleaning is unconditional, answering is conditional on `ip_asked == self.my_ip`.

### `on_reply()`

One function, three actions in sequence: `confirm()` the cache, `flush()` the queue, trace the outcome including the exact tuple of delivered packet labels. The delivered tuple is also this function's return value — `run_resolution()` passes it straight back to its own caller.

### `run_resolution()`

The whole track's payoff in nine lines. Read it as a script of two nodes' method calls, not as new logic — every call inside it is a method already covered above.

## Failure Questions

Use the source file to answer these:

1. In `on_request()`, if `from_mac` gleaned from the request differs from whatever `b`'s cache already held for `from_ip`, does the glean still overwrite it? Which function call proves this?
2. `send_to()` checks `result.state in (NeighborState.REACHABLE, NeighborState.STALE)` to decide whether to deliver immediately. Does a `STALE` mapping ever trigger a fresh `start_resolution()` call, or does it deliver using the old MAC?
3. If `send_to()` is called twice in a row for the same unresolved IP before any reply arrives, does the second call run `start_resolution()` again? What does `lookup()` return the second time that makes the difference?
4. `on_reply()` calls `flush(self.pending, announcement.ip)` before appending to `self.trace`. If the queue for that IP was already empty, what does `delivered` equal, and what does the trace line say?
5. `run_resolution()` returns `(packet_label,)` directly if `mac is not None` from the first `send_to()` call. Under what cache state would this early-return path trigger instead of the full who-has exchange?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/arp/session_04_walkthrough.py
```

The walkthrough builds two `ToyArpNode`s, runs `run_resolution()` and confirms the queued-and-delivered packet along with a who-has line in A's trace, checks that B gleaned A's mapping purely from handling the request, confirms A's cache now holds B's mapping after the reply, checks both traces are non-empty, and finally calls `send_to()` a second time to show the now-cached mapping delivers immediately with no new who-has line.

## Done When

The learner can say all of the following without looking at notes:

- "Every field on ToyArpNode belongs to an earlier session in this track; responder_loop.py only wires cache, pending, and the announcement shape together."
- "send_to() delivers immediately for REACHABLE or STALE, and queues-plus-asks for anything else."
- "on_request() gleans the asker's mapping before it even checks whether the request is about this node's own IP — gleaning is unconditional, answering is not."

## References

- RFC 826 (An Ethernet Address Resolution Protocol)
