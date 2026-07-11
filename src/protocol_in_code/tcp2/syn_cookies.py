from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum

# Time here is a coarse "counter" tick, not milliseconds - real Linux SYN cookies
# advance this counter roughly every 64 seconds so a stolen cookie has a short shelf
# life. The exact period doesn't matter to the arithmetic below; what matters is that
# it is coarser than a normal `now` clock, which is why this file takes a plain
# `counter: int` instead of the `now: int` used elsewhere in the course.
COUNTER_MASK = 0b11111  # 5 bits: counter mod 32

MSS_TABLE = (536, 1220, 1440, 1460)

_MSS_BITS = 2  # log2(len(MSS_TABLE))
_COUNTER_BITS = 5
_HASH_BITS = 32 - _MSS_BITS - _COUNTER_BITS  # 25 bits of hash on top


class CookieVerdict(str, Enum):
    VALID = "Valid"
    STALE_COUNTER = "StaleCounter"
    TAMPERED = "Tampered"


@dataclass(frozen=True)
class VerifyResult:
    verdict: CookieVerdict
    recovered_mss: int | None


def _hash_bits(secret: str, src_ip: str, src_port: int, dst_ip: str, dst_port: int, counter: int) -> int:
    """The only thing that makes a cookie unforgeable: a keyed hash of the connection identity."""
    payload = f"{secret}|{src_ip}|{src_port}|{dst_ip}|{dst_port}|{counter}".encode()
    digest = hashlib.sha256(payload).digest()
    full = int.from_bytes(digest[:4], "big")
    return full >> (32 - _HASH_BITS)


def encode_cookie(
    secret: str,
    src_ip: str,
    src_port: int,
    dst_ip: str,
    dst_port: int,
    mss_index: int,
    counter: int,
) -> int:
    """Fold identity, MSS choice, and a coarse timestamp into one 32-bit initial sequence number.

    Bit layout, top to bottom: [ 25 bits hash | 5 bits counter mod 32 | 2 bits mss_index ].
    The hash covers the counter and mss_index too, so tampering with either the low bits
    or the hash bits alone breaks verification - the three fields are bound together, not
    just concatenated. This IS the server's SYN-ACK sequence number; there is no separate
    "cookie field" on the wire, which is the whole point of a stateless SYN cookie.
    """
    if not (0 <= mss_index < len(MSS_TABLE)):
        raise ValueError(f"mss_index out of range: {mss_index}")

    counter_bits = counter & COUNTER_MASK
    hash_bits = _hash_bits(secret, src_ip, src_port, dst_ip, dst_port, counter_bits)

    return (hash_bits << (_COUNTER_BITS + _MSS_BITS)) | (counter_bits << _MSS_BITS) | mss_index


def verify_cookie(
    cookie: int,
    secret: str,
    src_ip: str,
    src_port: int,
    dst_ip: str,
    dst_port: int,
    current_counter: int,
    max_age: int = 2,
) -> VerifyResult:
    """The client's final ACK hands the cookie back as ack-1; recompute it and see if it still fits.

    This is the whole trick: when the SYN queue is full, the server stores NOTHING for a
    half-open connection. It answers the SYN with a SYN-ACK whose sequence number IS the
    cookie, and forgets the SYN ever arrived. If the client is real, its ACK arrives with
    ack == cookie + 1, and the server reconstructs just enough state - here, only the MSS
    index - to open the connection. What's lost: everything that isn't 2 bits of mss_index.
    Window scale, SACK-permitted, timestamps - options a normal SYN would have carried -
    are simply not encoded, because there are no spare bits for them. A cookie-recovered
    connection silently downgrades to whatever defaults the server picks; that's the real
    cost of carrying zero bytes of state under attack.

    Any single-bit corruption is rejected one way or another: flip a bit in the hash
    region and the recomputed hash no longer matches (TAMPERED); flip a bit in the
    counter region and the recomputed hash is checked against a counter that no longer
    matches what was actually encoded, which almost always also fails the hash check,
    but can coincidentally look like an old, expired counter instead (STALE_COUNTER).
    Either verdict means "do not trust this ACK."
    """
    mss_index = cookie & 0b11
    counter_bits = (cookie >> _MSS_BITS) & COUNTER_MASK
    hash_bits = cookie >> (_COUNTER_BITS + _MSS_BITS)

    age = (current_counter - counter_bits) & COUNTER_MASK
    if age > max_age:
        return VerifyResult(CookieVerdict.STALE_COUNTER, None)

    expected_hash = _hash_bits(secret, src_ip, src_port, dst_ip, dst_port, counter_bits)
    if expected_hash != hash_bits:
        return VerifyResult(CookieVerdict.TAMPERED, None)

    return VerifyResult(CookieVerdict.VALID, MSS_TABLE[mss_index])
