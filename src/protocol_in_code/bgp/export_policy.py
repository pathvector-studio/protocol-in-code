from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .best_path import PathCandidate


class PeerType(str, Enum):
    EBGP = "ebgp"
    IBGP = "ibgp"


@dataclass(frozen=True)
class ExportPolicy:
    local_as: int
    next_hop_self: bool = False
    deny_prefixes: tuple[str, ...] = ()
    extra_prepend_count: int = 0


def prepare_export(
    path: PathCandidate,
    peer_type: PeerType,
    policy: ExportPolicy,
) -> PathCandidate | None:
    if path.prefix in policy.deny_prefixes:
        return None

    exported = path
    if policy.next_hop_self:
        exported = replace(exported, next_hop="self")

    if peer_type is PeerType.EBGP:
        prepend_count = 1 + policy.extra_prepend_count
        exported = replace(
            exported,
            as_path=((policy.local_as,) * prepend_count) + exported.as_path,
        )

    return exported
