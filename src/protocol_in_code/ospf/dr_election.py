from __future__ import annotations

from dataclasses import dataclass


def _router_id_key(router_id: str) -> tuple[int, ...]:
    return tuple(int(part) for part in router_id.split("."))


@dataclass(frozen=True)
class InterfaceCandidate:
    router_id: str
    priority: int
    declared_dr: bool = False
    declared_bdr: bool = False


@dataclass(frozen=True)
class ElectionResult:
    designated_router: str | None
    backup_designated_router: str | None
    eligible_routers: tuple[str, ...]


def _pick_highest(candidates: list[InterfaceCandidate]) -> InterfaceCandidate | None:
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: (candidate.priority, _router_id_key(candidate.router_id)))


def elect_dr_bdr(candidates: tuple[InterfaceCandidate, ...]) -> ElectionResult:
    eligible = [candidate for candidate in candidates if candidate.priority > 0]
    declared_dr = [candidate for candidate in eligible if candidate.declared_dr]
    designated = _pick_highest(declared_dr) or _pick_highest(eligible)

    remaining = [candidate for candidate in eligible if designated is None or candidate.router_id != designated.router_id]
    declared_bdr = [candidate for candidate in remaining if candidate.declared_bdr]
    backup = _pick_highest(declared_bdr) or _pick_highest(remaining)

    return ElectionResult(
        designated_router=designated.router_id if designated else None,
        backup_designated_router=backup.router_id if backup else None,
        eligible_routers=tuple(candidate.router_id for candidate in sorted(eligible, key=lambda item: _router_id_key(item.router_id))),
    )

