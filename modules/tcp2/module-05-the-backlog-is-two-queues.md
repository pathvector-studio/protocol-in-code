# Session 05 / Module 05: The Backlog Is Two Queues

## Position

- Track: TCP2
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/tcp2/module-05/index.html`
- Source file: `src/protocol_in_code/tcp2/backlog.py`
- Walkthrough script: `examples/tcp2/session_05_walkthrough.py`

## Core Question

"The listen backlog" sounds like one number — so why does a single listening socket actually keep two separate queues, and what happens when each one fills up?

## Outcome

By the end of this session, the learner should be able to:

- name the two queues a `ListenBacklog` holds and who fills and drains each one
- trace what happens to a SYN once `syn_queue` is already full
- explain, precisely, what happens to both the client's ACK and the syn_queue entry when the accept queue is full
- explain why `UNKNOWN_CLIENT` is a distinct outcome from a full queue
- explain what `app_accept()` returns once the accept queue is empty

## Read Order

1. Read the module comment above `SynOutcome` — the two-queues, two-owners framing
2. Read `SynOutcome` and `AckOutcome`
3. Read `ListenBacklog`
4. Read `on_syn()`
5. Read `on_final_ack()`
6. Read `app_accept()`
7. Run `examples/tcp2/session_05_walkthrough.py`

## Read It Like Code

```python
ListenBacklog(
    syn_limit,
    accept_limit,
    syn_queue,     # dict[client_tuple, int] - half-open, kernel fills and drains
    accept_queue,  # list[client_tuple] - fully established, kernel fills, application drains
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `syn_queue` | Half-open connections: SYN seen, SYN-ACK sent, no final ACK yet. The kernel alone fills and drains this. |
| `accept_queue` | Fully-established connections waiting for `accept()`. The kernel fills it; the application drains it. |
| `syn_limit` / `accept_limit` | Independent caps — a slow application backs up `accept_queue` with no effect on `syn_queue`'s capacity, and vice versa. |

## Decision Flow

```text
on_syn(backlog, client_tuple, now):
  client_tuple already in syn_queue      -> QUEUED           (idempotent re-send)
  len(syn_queue) >= syn_limit            -> DROPPED_SYN_QUEUE_FULL
  otherwise                              -> QUEUED            (insert, stamped with now)

on_final_ack(backlog, client_tuple):
  client_tuple not in syn_queue          -> UNKNOWN_CLIENT
  len(accept_queue) >= accept_limit      -> ACCEPT_QUEUE_FULL  (ACK is dropped; syn_queue entry stays put)
  otherwise                              -> MOVED_TO_ACCEPT_QUEUE  (delete from syn_queue, append to accept_queue)

app_accept(backlog):
  accept_queue empty                     -> None
  otherwise                              -> pop the oldest entry (FIFO)
```

## Reading Lens

The important move in this session is to stop asking "is the backlog full?" — there is no single backlog — and start asking, for any given moment:

- which queue is this event about, `syn_queue` or `accept_queue`?
- who is responsible for draining that queue — the kernel on its own, or does it wait on the application?
- if this queue is full right now, what specifically happens to the packet that triggered the check — is it dropped, or just left where it was?

The accept-queue-full case is the one worth sitting with the longest: `on_final_ack()` does not reset the connection and does not touch `syn_queue` at all when `accept_queue` is full. The client's final ACK is silently dropped, and the half-open entry is left exactly where it already was, as if the ACK had never arrived. The eerie consequence: the client believes the handshake finished — it sent its ACK, heard nothing back, and by TCP's rules that's a completed active open, no reply expected. But the server has no record of an established connection, only a half-open entry sitting in `syn_queue`. Nothing is wrong from the client's point of view until the client tries to send data and gets no response, or until its own retransmit timer eventually resends a segment the server will read as a new final ACK — a second chance that only works if the application has drained `accept_queue` by then.

## Toy Model Boundary

Real listen sockets track substantially more per half-open entry — retransmitted SYN-ACKs, a timer per entry, and (per `syn_cookies.py`, see below) a fallback to stateless cookies once `syn_queue` is under pressure, rather than an outright drop. This module keeps `on_syn()`'s `DROPPED_SYN_QUEUE_FULL` as a naive fixed-size-queue drop precisely so the "queue is full" moment is visible as its own outcome; `janitor_loop.py` (Session 06) is where cookie-mode actually replaces that drop. There is also no timeout modeled anywhere in this file — a `now: int` is threaded through `on_syn()` for parity with the rest of the course, but nothing in `backlog.py` itself ever expires a `syn_queue` entry on its own.

## Code Landmarks

### The module comment above `SynOutcome`

Names the two queues, their two owners, and the independence of their failure modes before any function is read — the frame the whole file hangs on.

### `on_syn()`

The `client_tuple in backlog.syn_queue` check runs before the capacity check — a duplicate SYN for an already-queued client returns `QUEUED` again rather than being evaluated against `syn_limit` a second time.

### `on_final_ack()`'s docstring

Spells out the Linux behavior directly: on `ACCEPT_QUEUE_FULL`, "the half-open entry stays in the syn_queue, the client's ACK is simply not answered." This is the single most important sentence in the file.

### `app_accept()`

`pop(0)` — FIFO, oldest connection first. One line, and the only place `accept_queue` shrinks.

## Failure Questions

Use the source file to answer these:

1. `on_final_ack()` is called for a `client_tuple` while `accept_queue` is at `accept_limit`. What happens to that `client_tuple`'s entry in `syn_queue` — is it deleted, modified, or untouched? Which line (or absence of a line) proves it?
2. A SYN arrives for a `client_tuple` already present in `syn_queue`. Does `on_syn()` check it against `syn_limit`? What does it return?
3. `on_final_ack()` is called for a `client_tuple` that was never seen by `on_syn()`. What outcome is returned, and how does that differ from what would happen if `syn_queue` were merely full?
4. `app_accept()` is called when `accept_queue` is empty. What does it return, and what does the caller have to check before treating the result as a connection?
5. Two different client tuples both send a final ACK while `accept_queue` has exactly one open slot. Does the order the two `on_final_ack()` calls happen in matter to which one succeeds? Why or why not, based on the function's logic?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tcp2/session_05_walkthrough.py
```

The walkthrough fills `syn_queue` to its limit and shows the next SYN dropped, moves a queued client to the accept queue on its final ACK, fills the accept queue and shows the next final ACK dropped while its syn_queue entry survives untouched, sends a final ACK for a client that never sent a SYN, and drains the accept queue with `app_accept()` down to `None`.

## Done When

The learner can say all of the following without looking at notes:

- "The backlog is two queues, not one: syn_queue is half-open connections the kernel alone manages, accept_queue is finished connections waiting on the application."
- "A full syn_queue drops the SYN. A full accept_queue drops the final ACK instead — and leaves the syn_queue entry exactly where it was."
- "The two queues fail independently: a slow application can back up accept_queue while syn_queue has room to spare, and vice versa."

## References

- Listen backlog behavior described here follows Linux's and BSD's socket implementations (the two-queue split, and dropping rather than resetting on a full accept queue) — there is no single RFC that specifies this; it is documented kernel/socket-API behavior, not a protocol requirement.
