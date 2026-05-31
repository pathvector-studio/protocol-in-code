from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PathAttributes:
    next_hop: str
    as_path: tuple[int, ...]
    origin: str
    local_pref: int = 100


@dataclass(frozen=True)
class BGPUpdate:
    nlri: tuple[str, ...] = ()
    withdrawn_routes: tuple[str, ...] = ()
    path_attributes: PathAttributes | None = None


@dataclass
class RoutingTable:
    paths_by_prefix: dict[str, list[PathAttributes]] = field(default_factory=dict)

    def apply_update(self, prefix: str, attributes: PathAttributes) -> None:
        self.paths_by_prefix.setdefault(prefix, []).append(attributes)

    def withdraw(self, prefix: str) -> None:
        self.paths_by_prefix.pop(prefix, None)


def apply_update_message(table: RoutingTable, update: BGPUpdate) -> RoutingTable:
    """Apply withdrawals first, then announcements from a single UPDATE."""
    for prefix in update.withdrawn_routes:
        table.withdraw(prefix)

    if update.path_attributes is None:
        return table

    for prefix in update.nlri:
        table.apply_update(prefix, update.path_attributes)

    return table
