from __future__ import annotations

from dataclasses import dataclass, replace

from .best_path import PathCandidate
from .validation import ValidationState


@dataclass(frozen=True)
class ImportPolicy:
    local_pref_override: int | None = None
    weight: int = 0
    reject_next_hops: tuple[str, ...] = ()
    reject_invalid: bool = False


def apply_import_policy(
    candidate: PathCandidate,
    validation_state: ValidationState,
    policy: ImportPolicy,
) -> PathCandidate | None:
    if candidate.next_hop in policy.reject_next_hops:
        return None

    if validation_state is ValidationState.INVALID and policy.reject_invalid:
        return None

    updated = candidate
    if policy.local_pref_override is not None:
        updated = replace(updated, local_pref=policy.local_pref_override)
    if policy.weight != updated.weight:
        updated = replace(updated, weight=policy.weight)
    return updated
