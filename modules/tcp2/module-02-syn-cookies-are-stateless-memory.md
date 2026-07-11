# Session 02 / Module 02: SYN Cookies Are Stateless Memory

## Position

- Track: TCP2
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/tcp2/module-02/index.html`
- Source file: `src/protocol_in_code/tcp2/syn_cookies.py`
- Walkthrough script: `examples/tcp2/session_02_walkthrough.py`

## Core Question

When the SYN queue is full and the server refuses to remember a half-open connection, how does it still recognize a real client's ACK three steps later?

## Outcome

By the end of this session, the learner should be able to:

- explain why the SYN-ACK sequence number IS the cookie, not a separate field
- name the three fields folded into a cookie's 32 bits and how many bits each gets
- explain why a cookie is a keyed proof and not a lookup key — why a different secret can never verify one
- list what a cookie-recovered connection loses that a normal handshake would have kept

## Read Order

1. Read the module docstring on `COUNTER_MASK` (why a coarse counter, not `now`)
2. Read `MSS_TABLE` and the bit-width constants
3. Read `CookieVerdict` and `VerifyResult`
4. Read `_hash_bits()`
5. Read `encode_cookie()`
6. Read `verify_cookie()`
7. Run `examples/tcp2/session_02_walkthrough.py`

## Read It Like Code

```python
VerifyResult(
    verdict,
    recovered_mss,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `verdict` | One of `VALID`, `STALE_COUNTER`, `TAMPERED` — the only three outcomes verification can reach. |
| `recovered_mss` | The one piece of connection state a cookie can carry back. `None` on anything but `VALID`. |

## Decision Flow

```text
verify_cookie(cookie, secret, ...):
    unpack mss_index, counter_bits, hash_bits from the cookie's 32 bits

    age = (current_counter - counter_bits) mod 32
    age > max_age                       -> STALE_COUNTER (recovered_mss=None)

    recompute expected_hash from secret + identity + counter_bits
    expected_hash != hash_bits          -> TAMPERED      (recovered_mss=None)

    otherwise                           -> VALID          (recovered_mss=MSS_TABLE[mss_index])
```

## Reading Lens

The important move in this session is to stop asking "what does the server remember about this connection" and start asking:

- where is the state that used to live in a SYN queue entry — is it stored anywhere, or is it being recomputed?
- which of the 32 bits does the hash actually cover — just itself, or the counter and MSS too?
- what happens to everything a normal SYN would have negotiated that isn't the MSS?

## Toy Model Boundary

Real SYN cookie implementations (originally D.J. Bernstein's technique, later adopted broadly) encode the timestamp counter with more care than this file's flat 5-bit mod-32 value, and some variants steal a bit to signal "SACK permitted" instead of leaving it unencoded entirely. This file keeps the bit budget brutally simple — 25 bits hash, 5 bits counter, 2 bits MSS index — so the "what gets thrown away" lesson stays visible instead of buried in wire-format detail. The secret in this toy is a plain string passed as a function argument; a real server holds a secret that itself rotates on a schedule independent of the counter, which this file does not model.

## Code Landmarks

### `_hash_bits()`

The only thing standing between an attacker and a forged cookie: a SHA-256 hash keyed by `secret`, truncated to 25 bits. It hashes `counter_bits`, not the raw `counter` argument — `encode_cookie()` and `verify_cookie()` both mask to 5 bits before hashing, which is why tampering with the counter portion of a cookie almost always also breaks the hash check.

### `encode_cookie()`

The whole point of a stateless cookie in one return line: `(hash_bits << 7) | (counter_bits << 2) | mss_index`. There is no dictionary, no queue entry, nothing kept in memory after this call returns. The cookie itself IS what gets sent as the SYN-ACK's sequence number.

### `verify_cookie()`

Reconstructs the three fields by unshifting the same bit positions `encode_cookie()` used, checks staleness before authenticity — an old cookie is rejected before the hash is even recomputed — and only on the `VALID` path does it look up `MSS_TABLE[mss_index]` to hand back the one piece of state that survived.

## Failure Questions

Use the source file to answer these:

1. `_hash_bits()` is called with `counter_bits`, the masked 5-bit value — not the raw `counter` passed into `encode_cookie()`. Why does hashing the masked value, rather than the raw counter, matter for what `verify_cookie()` can check?
2. Which bits does `expected_hash` in `verify_cookie()` actually cover — just the hash region of the cookie, or the counter and MSS index too? Which line in `_hash_bits()`'s docstring says so?
3. `verify_cookie()` checks `age > max_age` before it checks the hash. If you flip a bit in the cookie's counter region, which verdict is likely, and why does the docstring say it "almost always" also fails the hash check rather than always?
4. What does `verify_cookie()` return for `recovered_mss` on every verdict except `VALID`? Why must it be `None` rather than some default MSS?
5. If two servers computed cookies for the same connection identity and counter but used different `secret` values, could either one's `verify_cookie()` ever accept the other's cookie? Which line makes that impossible?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tcp2/session_02_walkthrough.py
```

The walkthrough encodes a cookie with `mss_index` pointing at 1460 and confirms it round-trips to `VALID` with `recovered_mss == 1460`, flips a bit in the hash region to produce `TAMPERED`, ages the counter past `max_age` to produce `STALE_COUNTER`, confirms the boundary at exactly `max_age` is still `VALID`, and shows a different secret can never verify the same cookie — the headline: a cookie is a keyed proof, not a lookup.

## Done When

The learner can say all of the following without looking at notes:

- "The cookie doesn't get looked up anywhere — it gets recomputed and compared. There is nothing stored to look up."
- "The hash covers the counter and MSS index too, so you can't tamper with the low bits without also breaking the hash check."
- "A cookie only remembers 2 bits worth of state — the MSS index. Window scale, SACK, timestamps: all gone, and that's the price of statelessness under attack."

## References

- SYN cookies are attributed to D.J. Bernstein's technique; no RFC governs the technique itself.
- RFC 4987 (TCP SYN Flooding Attacks and Common Mitigations — surveys SYN cookies among other mitigations, without specifying the cookie encoding).
