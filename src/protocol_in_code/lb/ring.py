"""The ring survives a server change.

hash_pick.py folds a client key onto `len(backends)` directly, so every
membership change reshuffles the divisor and remaps almost every key (see
its `remap_fraction`). Consistent hashing fixes this by never dividing by
the backend count at all: backends and keys are both hashed onto the same
fixed circle (positions 0 to 2**256-1, here), and a key is served by the
first backend at or after its position going clockwise. Add or remove one
backend and only the keys between its neighbor and it move — everyone
else's nearest clockwise backend is unchanged.

Each backend claims multiple points on the circle ("virtual nodes") rather
than one, so that removing a single backend doesn't dump its entire share
onto whichever one neighbor happened to sit next to it on the circle —
the load spreads across many neighbors instead of one.
"""

from __future__ import annotations

import bisect
import hashlib


def _hash_int(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest(), 16)


def build_ring(backends: tuple[str, ...], vnodes_per_backend: int) -> tuple[tuple[int, str], ...]:
    """Hash `vnodes_per_backend` points per backend onto the circle and sort by position.

    Each point is `hash(f"{backend}#{i}")` for i in range(vnodes_per_backend).
    More vnodes means a smoother distribution and a smaller share moving
    per membership change, at the cost of a larger ring to build and search.
    """
    points = [
        (_hash_int(f"{backend}#{i}"), backend)
        for backend in backends
        for i in range(vnodes_per_backend)
    ]
    return tuple(sorted(points))


def pick(ring: tuple[tuple[int, str], ...], client_key: str) -> str:
    """Find the first ring position at or after the key's hash, wrapping to the start.

    The ring is sorted by position, so "first point clockwise from here" is
    exactly what binary search answers: `bisect_left` finds the insertion
    index for the key's hash, and that index's backend (or the ring's first
    entry, if the key hashes past the last point) is the pick. The ring
    lookup IS binary search — nothing more is required once the points are sorted.
    """
    if not ring:
        raise ValueError("no backends to pick from")

    positions = [position for position, _ in ring]
    index = bisect.bisect_left(positions, _hash_int(client_key))
    if index == len(ring):
        index = 0
    return ring[index][1]


def remap_fraction(
    backends_before: tuple[str, ...],
    backends_after: tuple[str, ...],
    sample_keys: tuple[str, ...],
    vnodes_per_backend: int,
) -> float:
    """Same signature as hash_pick.remap_fraction, same question, much smaller answer.

    Only the keys that fell between the changed backend's vnodes and its
    neighbors move. In expectation that is close to 1/n of the keys for an
    n-to-(n+1) growth, not the (n-1)/n that modulo hashing costs.
    """
    if not sample_keys:
        return 0.0

    ring_before = build_ring(backends_before, vnodes_per_backend)
    ring_after = build_ring(backends_after, vnodes_per_backend)

    remapped = sum(
        1
        for key in sample_keys
        if pick(ring_before, key) != pick(ring_after, key)
    )
    return remapped / len(sample_keys)
