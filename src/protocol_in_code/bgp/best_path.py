from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PathCandidate:
    prefix: str
    next_hop: str
    weight: int = 0
    local_pref: int = 100
    as_path: tuple[int, ...] = ()
    origin_type: int = 0


def _is_better(candidate: PathCandidate, current: PathCandidate) -> bool:
    if candidate.weight != current.weight:
        return candidate.weight > current.weight
    if candidate.local_pref != current.local_pref:
        return candidate.local_pref > current.local_pref
    if len(candidate.as_path) != len(current.as_path):
        return len(candidate.as_path) < len(current.as_path)
    if candidate.origin_type != current.origin_type:
        return candidate.origin_type < current.origin_type
    return candidate.next_hop < current.next_hop


def select_best_path(paths: list[PathCandidate]) -> PathCandidate:
    if not paths:
        raise ValueError("at least one path is required")

    best = paths[0]
    for candidate in paths[1:]:
        if candidate.prefix != best.prefix:
            raise ValueError("all compared paths must be for the same prefix")
        if _is_better(candidate, best):
            best = candidate
    return best
