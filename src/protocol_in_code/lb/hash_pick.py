"""Hashing keeps you on the same server.

Round robin (round_robin.py) and least connections (least_conn.py) both
answer "which backend is least burdened right now" — neither promises that
the *same* client lands on the *same* backend twice. Session affinity needs
that promise, and hashing is the obvious way to get it: turn the client's
key into a number, fold it onto the backend list with modulo, and the same
key always folds onto the same backend, no state required.

That "no state required" is also the flaw. The fold depends on
`len(backends)`. Change the backend count — one server dies, one is added
for capacity — and `hash(key) % n` changes for almost every key, not just
the ones that needed to move. `remap_fraction` below measures exactly how
much churn that one-server change causes; ring.py exists to fix it.
"""

from __future__ import annotations

import hashlib


def _hash_int(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest(), 16)


def pick(backends: tuple[str, ...], client_key: str) -> str:
    """Fold the client key onto the backend list: same key, same backend, until `backends` changes."""
    if not backends:
        raise ValueError("no backends to pick from")

    index = _hash_int(client_key) % len(backends)
    return backends[index]


def remap_fraction(
    backends_before: tuple[str, ...],
    backends_after: tuple[str, ...],
    sample_keys: tuple[str, ...],
) -> float:
    """What fraction of `sample_keys` land on a different backend after the membership change?

    This is the honest cost of modulo hashing: because the fold is
    `hash(key) % len(backends)`, changing `len(backends)` by even one
    changes the divisor for every key, and the remainder is unrelated
    between divisors n and n+1. In expectation, growing or shrinking the
    backend set by one remaps close to (n-1)/n of all keys — almost
    everyone moves, not just the keys that had to.
    """
    if not sample_keys:
        return 0.0

    remapped = sum(
        1
        for key in sample_keys
        if pick(backends_before, key) != pick(backends_after, key)
    )
    return remapped / len(sample_keys)
