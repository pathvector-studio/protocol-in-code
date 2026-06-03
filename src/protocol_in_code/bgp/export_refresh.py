from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .best_path import PathCandidate
from .export_policy import ExportPolicy, PeerType, prepare_export
from .ribs import AdjRIBOut, LocRIB


class ExportChangeKind(str, Enum):
    ADVERTISE = "advertise"
    WITHDRAW = "withdraw"


@dataclass(frozen=True)
class ExportTarget:
    peer_id: str
    peer_type: PeerType
    policy: ExportPolicy


@dataclass(frozen=True)
class ExportChange:
    peer_id: str
    prefix: str
    kind: ExportChangeKind
    path: PathCandidate | None


def refresh_exports_for_prefix(
    prefix: str,
    loc_rib: LocRIB,
    adj_rib_out: AdjRIBOut,
    targets: tuple[ExportTarget, ...],
) -> list[ExportChange]:
    installed = loc_rib.best_paths.get(prefix)
    changes: list[ExportChange] = []

    for target in targets:
        current_by_prefix = adj_rib_out.advertisements_by_peer.setdefault(target.peer_id, {})
        current = current_by_prefix.get(prefix)
        desired = None
        if installed is not None:
            desired = prepare_export(installed, target.peer_type, target.policy)

        if desired is None:
            if current is not None:
                current_by_prefix.pop(prefix, None)
                changes.append(
                    ExportChange(
                        peer_id=target.peer_id,
                        prefix=prefix,
                        kind=ExportChangeKind.WITHDRAW,
                        path=None,
                    )
                )
            continue

        if current != desired:
            current_by_prefix[prefix] = desired
            changes.append(
                ExportChange(
                    peer_id=target.peer_id,
                    prefix=prefix,
                    kind=ExportChangeKind.ADVERTISE,
                    path=desired,
                )
            )

    return changes
