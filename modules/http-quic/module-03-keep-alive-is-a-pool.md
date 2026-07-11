# Session 03 / Module 03: Keep-Alive Is a Pool

## Position

- Track: HTTP/QUIC
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/http-quic/module-03/index.html`
- Source file: `src/protocol_in_code/http/pool.py`
- Walkthrough script: `examples/http-quic/session_03_walkthrough.py`

## Core Question

When a client wants a connection to a host, how does it decide between reusing something idle and opening something new — and what makes an idle connection stop being reusable?

## Outcome

By the end of this session, the learner should be able to:

- name the two `CheckoutOutcome` values and what triggers each
- state `IDLE_TIMEOUT` and explain the exact comparison that enforces it
- explain what happens, in order, inside `checkout()` before a decision is made
- explain why the connection evicted at the boundary is gone, not merely stale-but-usable

## Read Order

1. Read `IDLE_TIMEOUT` and `CheckoutOutcome`
2. Read `IdleConnection` and `ConnectionPool`
3. Read `_evict_expired()`
4. Read `checkout()`
5. Read `checkin()`
6. Run `examples/http-quic/session_03_walkthrough.py`

## Read It Like Code

```python
ConnectionPool(
    idle,          # dict[str, list[IdleConnection]]
    next_conn_id,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `idle` | Keyed by host. Each host has its own list of idle connections — nothing is shared across hosts. |
| `next_conn_id` | A single counter across the whole pool, not per host. Connection identity is pool-wide even though eviction and reuse are host-scoped. |
| `IdleConnection.idle_since` | The `now` at which the connection was checked in. Staleness is computed from this, not tracked by a timer. |
| `IDLE_TIMEOUT` | `30`. The single constant that defines how long an idle connection stays reusable. |

## Decision Flow

```text
checkout(pool, host, now):
    evict every idle connection for host where now - idle_since >= IDLE_TIMEOUT
    pool.idle[host] non-empty after eviction -> pop last, return REUSED with its conn_id
    otherwise                                -> mint next_conn_id, return NEW
```

## Reading Lens

The important move in this session is to stop thinking of "keep-alive" as a flag on a connection and start asking:

- which host's list is being touched, and is it disjoint from every other host's list?
- what is `now - idle_since` at the moment of eviction, and does the comparison keep or evict at the exact boundary?
- does `checkout()` evict *before* or *after* checking whether there's something to reuse — and what would break if that order were reversed?

## Toy Model Boundary

Real HTTP client connection pools enforce a maximum pool size, a per-host connection limit, and often distinguish idle-timeout from a separate keep-alive-max (a server-advertised request count or duration). `ConnectionPool` here has neither cap: `idle[host]` can grow without bound between checkouts, and there is no upper limit on how many connections `checkout()` will mint. Eviction is also purely lazy — it only happens inside `checkout()`, on the host being requested, not on a background sweep across the whole pool. This is the same expiry-is-arithmetic shape as the DNS cache from the DNS track: staleness is `now - stored_at` compared against a constant, not a callback firing in real time.

## Code Landmarks

### `IDLE_TIMEOUT = 30`

A module-level constant, not a field on `ConnectionPool`. Every host uses the same timeout — there is no per-host override anywhere in this file.

### `_evict_expired()`

```python
def _evict_expired(pool: ConnectionPool, host: str, now: int) -> None:
    connections = pool.idle.get(host, [])
    pool.idle[host] = [c for c in connections if now - c.idle_since < IDLE_TIMEOUT]
```

The keep condition is strict `<`. A connection checked in at `idle_since=10`, checked against at `now=40`, has `now - idle_since == 30 == IDLE_TIMEOUT` — that is *not* less than `IDLE_TIMEOUT`, so it fails the keep condition and is evicted. The boundary belongs to eviction, not to reuse: at exactly `idle_since + IDLE_TIMEOUT`, the connection is gone.

### `checkout()` — order of operations

```python
def checkout(pool: ConnectionPool, host: str, now: int) -> CheckoutResult:
    _evict_expired(pool, host, now)

    connections = pool.idle.get(host, [])
    if connections:
        reused = connections.pop()
        return CheckoutResult(CheckoutOutcome.REUSED, reused.conn_id)

    conn_id = pool.next_conn_id
    pool.next_conn_id += 1
    return CheckoutResult(CheckoutOutcome.NEW, conn_id)
```

Eviction runs unconditionally, first, every single call — even if the caller only cares about reuse. There is no way to check out a connection without first paying the eviction cost for that host. `connections.pop()` removes from the *end* of the list, which is also the end `checkin()` appends to, making this a LIFO stack per host, not a FIFO queue.

### `checkin()`

```python
def checkin(pool: ConnectionPool, host: str, conn_id: int, now: int) -> None:
    pool.idle.setdefault(host, []).append(IdleConnection(conn_id, now))
```

Stamps `idle_since=now` at the moment of return, not at the moment the connection was originally minted. A connection reused many times just keeps getting a fresh idle clock each time it comes back — its age as an idle *connection* has nothing to do with how long ago it was first created.

## Failure Questions

Use the source file to answer these:

1. A connection is checked in at `now=10`. At `now=39`, is it still reusable? At `now=40`? Which comparison in `_evict_expired()` decides, and which one of those two calls evicts it?
2. `checkout()` is called for `"a.com"` while `pool.idle["b.com"]` has three stale entries. Does anything about `"b.com"`'s list change? Why or why not?
3. If `checkin()` is never called after a `NEW` checkout, does the minted `conn_id` ever appear in `pool.idle`? What does that imply about connections currently in use?
4. Two connections for the same host are checked in at `now=0` and `now=5`. A checkout happens at `now=10` and succeeds as `REUSED`. Which `conn_id` comes back — the one checked in at `0` or at `5`? Which line decides?
5. Does `_evict_expired()` run before or after the pool checks whether it has something to reuse? What would change about the boundary behavior in Failure Question 1 if that order were swapped?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/http-quic/session_03_walkthrough.py
```

The walkthrough checks out a fresh connection, reuses it after checkin, lets it expire past the timeout, hits the exact `IDLE_TIMEOUT` boundary, reuses one just inside the boundary, and checks out a different host to show the pools don't interact.

## Done When

The learner can say all of the following without looking at notes:

- "Idle connections are pooled per host; nothing is ever shared or evicted across hosts by the same call."
- "The keep condition is `now - idle_since < IDLE_TIMEOUT`, so at exactly `IDLE_TIMEOUT` the connection is evicted, not kept."
- "Eviction always runs first, on every checkout, before the pool decides between REUSED and NEW."

## References

- RFC 9112 Section 9 (Message Transfer and Persistence)
