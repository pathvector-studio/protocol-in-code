# Session 02 / Module 02: Packets Wait for Answers

## Position

- Track: ARP/ND
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/arp/module-02/index.html`
- Source file: `src/protocol_in_code/arp/pending.py`
- Walkthrough script: `examples/arp/session_02_walkthrough.py`

## Core Question

While an IP address is still unresolved, where does the packet that wanted to go there actually go?

## Outcome

By the end of this session, the learner should be able to:

- explain why the IP layer doesn't block waiting for an ARP reply
- name the cap on how many packets can wait behind one unresolved IP
- explain exactly which packet gets dropped when that cap is exceeded
- describe what `flush()` and `drop_all()` each do to the queue, and when the responder loop calls which one

## Read Order

1. Read the module comment at the top of the file
2. Read `PendingQueue`
3. Read `enqueue()`
4. Read `flush()`
5. Read `drop_all()`
6. Run `examples/arp/session_02_walkthrough.py`

## Read It Like Code

```python
PendingQueue(
    waiting,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `waiting` | One tuple per destination IP — the line of packets parked behind an unresolved mapping. |

## Decision Flow

```text
enqueue appends the new packet, then checks length:
  len(updated) > MAX_QUEUE_PER_IP -> slice to the LAST MAX_QUEUE_PER_IP entries, return QUEUED_DROPPED_OLDEST
  otherwise                       -> keep everything, return QUEUED

flush(ip)    -> pop and return the whole tuple for that IP (queue for that IP is now gone)
drop_all(ip) -> pop and discard the whole tuple for that IP (nothing is returned)
```

## Reading Lens

The important move in this session is to stop thinking of ARP resolution as something the sender blocks on and start asking:

- where does a packet physically sit while its destination is unresolved?
- when the line for one IP is full, which packet is sacrificed — the newest arrival or the oldest one already waiting?
- does completing resolution give the packets back, or does failing resolution give them back?

## Toy Model Boundary

Real IP stacks queue at the interface or neighbor-cache level with hardware and driver-specific limits, and some implementations queue only the single most recent packet per destination rather than a short FIFO. This toy fixes `MAX_QUEUE_PER_IP = 3` for every destination and uses a plain tuple slice to drop the oldest, which keeps the eviction rule readable as one line of code instead of a configurable policy. There's no notion of packet priority, size, or per-queue timeout here — a packet parked in `PendingQueue.waiting` sits there until `flush()` or `drop_all()` is called explicitly by the responder loop; nothing here times it out on its own.

## Code Landmarks

### The module comment

Names the thesis directly: "the IP layer doesn't block on ARP." A packet to an unresolved destination parks in a line instead of stalling the sender.

### `enqueue()`

The main reading target. It always appends first — `current + (packet_label,)` — and only afterward checks whether the result is too long. The drop is a **slice**, `updated[-MAX_QUEUE_PER_IP:]`, which keeps the most recent `MAX_QUEUE_PER_IP` entries and discards everything before them — drop-oldest, not drop-newest.

### `flush()`

`queue.waiting.pop(ip, ())` — this is a genuine pop, not a copy-and-clear. After `flush()`, the IP has no entry in `waiting` at all, which matters if you check `ip in queue.waiting` afterward.

### `drop_all()`

Nearly identical to `flush()` — `queue.waiting.pop(ip, None)` — but the return value is thrown away by the caller's intent, not by the function signature. `drop_all()` still returns via `pop`, it's just that nobody is meant to read what comes back; the whole point is resolution failed and there is nothing deliverable.

## Failure Questions

Use the source file to answer these:

1. Four packets are enqueued in order `p1, p2, p3, p4` for the same IP. Which three survive, and what outcome value does the fourth `enqueue()` call return?
2. What does `enqueue()` return on the very first packet for a brand-new IP — is it ever `QUEUED_DROPPED_OLDEST` on the first call?
3. After `flush(queue, ip)` runs, what does `queue.waiting.get(ip)` return if you call `enqueue()` again for that same IP right after?
4. What is the return type of `drop_all()`, and does its caller in this module ever use the return value?
5. If `MAX_QUEUE_PER_IP` packets are already queued and one more arrives, exactly how many packets are in `queue.waiting[ip]` immediately after that call?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/arp/session_02_walkthrough.py
```

The walkthrough queues three packets in order, queues a fourth to show the oldest gets dropped, flushes the survivors and confirms the line empties, and separately shows `drop_all()` discarding a queue without returning anything useful.

## Done When

The learner can say all of the following without looking at notes:

- "The IP layer never blocks on ARP — an unresolved packet parks in a per-IP queue instead."
- "The queue caps at MAX_QUEUE_PER_IP and drops the oldest packet, not the newest, once it's full."
- "flush() hands back everything and empties the line; drop_all() empties the line and hands back nothing anyone uses."

## References

- RFC 826 (An Ethernet Address Resolution Protocol)
