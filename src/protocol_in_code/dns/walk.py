from __future__ import annotations

from dataclasses import dataclass, field

from .query import DNSQuestion, normalize_name

MAX_WALK_STEPS = 8

ROOT_ZONE = ""


@dataclass(frozen=True)
class Zone:
    """One authoritative vantage point in the tree, keyed by what it knows directly."""

    name: str
    answers: dict[tuple[str, str], tuple[str, ...]] = field(default_factory=dict)
    delegations: tuple[str, ...] = ()


@dataclass(frozen=True)
class WalkResult:
    found: bool
    records: tuple[str, ...]
    path: tuple[str, ...]
    stopped_because: str


def zone_covers(zone_name: str, qname: str) -> bool:
    """A zone covers a name when the name is inside that zone's subtree."""
    if zone_name == ROOT_ZONE:
        return True
    return qname == zone_name or qname.endswith("." + zone_name)


def pick_delegation(zone: Zone, qname: str) -> str | None:
    """Choose the most specific child zone that still covers the name."""
    best: str | None = None
    for child in zone.delegations:
        if not zone_covers(child, qname):
            continue
        if best is None or len(child) > len(best):
            best = child
    return best


def walk_from_root(
    question: DNSQuestion,
    zones: dict[str, Zone],
    max_steps: int = MAX_WALK_STEPS,
) -> WalkResult:
    """Descend from the root, one referral at a time, until an answer or a dead end."""
    qname = normalize_name(question.qname)
    current = ROOT_ZONE
    path: list[str] = []

    for _ in range(max_steps):
        zone = zones.get(current)
        if zone is None:
            return WalkResult(False, (), tuple(path), "delegation points to a missing zone")

        path.append(zone.name or ".")

        records = zone.answers.get((qname, question.qtype))
        if records:
            return WalkResult(True, records, tuple(path), "answer")

        child = pick_delegation(zone, qname)
        if child is None:
            return WalkResult(False, (), tuple(path), "no answer and no matching delegation")

        current = child

    return WalkResult(False, (), tuple(path), "step limit reached")
