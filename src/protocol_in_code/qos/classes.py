"""Classes form a tree.

Hierarchical shaping — the kind where "video" and "bulk" both live under "default" and
share whatever "default" doesn't use — is not a special algorithm. It is a tree: nodes
with a parent pointer, walked to check for unknown parents, cycles, and over-subscription,
the same three failure modes every tree-shaped config format has to guard against.

The `borrowable` rule picked here is deliberately the simplest honest one: a class's
borrowable capacity is its own unused guarantee (guaranteed_rate minus what its children
already claim) plus whatever its parent can, in turn, borrow — computed by walking up to
the root and summing each ancestor's own slack. It does not model sibling contention,
work-conserving redistribution, or bandwidth actually in flight; those need a live
scheduler, not a static tree walk. This function answers one question only: "if this class
needed more than its guarantee, how much slack does the chain above it have on paper?"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ValidationOutcome(str, Enum):
    VALID = "Valid"
    UNKNOWN_PARENT = "UnknownParent"
    CYCLE = "Cycle"
    OVER_SUBSCRIBED = "OverSubscribed"


@dataclass(frozen=True)
class TrafficClass:
    name: str
    guaranteed_rate: int
    parent: str | None = None


@dataclass
class ClassTree:
    classes: dict[str, TrafficClass] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationResult:
    outcome: ValidationOutcome
    detail: str


def validate_tree(tree: ClassTree) -> ValidationResult:
    """Three passes: every parent must exist, no class may be its own ancestor, no
    parent's children may promise more than the parent itself guarantees."""
    for cls in tree.classes.values():
        if cls.parent is not None and cls.parent not in tree.classes:
            return ValidationResult(ValidationOutcome.UNKNOWN_PARENT, f"{cls.name} -> {cls.parent}")

    for cls in tree.classes.values():
        visited: set[str] = set()
        current: str | None = cls.name
        while current is not None:
            if current in visited:
                return ValidationResult(ValidationOutcome.CYCLE, f"cycle reached at {current}")
            visited.add(current)
            current = tree.classes[current].parent

    children_sum: dict[str, int] = {}
    for cls in tree.classes.values():
        if cls.parent is not None:
            children_sum[cls.parent] = children_sum.get(cls.parent, 0) + cls.guaranteed_rate

    for parent_name, total in children_sum.items():
        parent = tree.classes[parent_name]
        if total > parent.guaranteed_rate:
            return ValidationResult(
                ValidationOutcome.OVER_SUBSCRIBED,
                f"{parent_name}: children claim {total} > guaranteed {parent.guaranteed_rate}",
            )

    return ValidationResult(ValidationOutcome.VALID, "")


def borrowable(tree: ClassTree, class_name: str) -> int:
    """Own unused guarantee, plus every ancestor's own unused guarantee, summed to the root."""
    children_sum: dict[str, int] = {}
    for cls in tree.classes.values():
        if cls.parent is not None:
            children_sum[cls.parent] = children_sum.get(cls.parent, 0) + cls.guaranteed_rate

    total = 0
    current: str | None = class_name
    while current is not None:
        cls = tree.classes[current]
        used_by_children = children_sum.get(current, 0)
        total += max(cls.guaranteed_rate - used_by_children, 0)
        current = cls.parent

    return total


if __name__ == "__main__":
    good = ClassTree(
        classes={
            "default": TrafficClass("default", guaranteed_rate=100, parent=None),
            "video": TrafficClass("video", guaranteed_rate=60, parent="default"),
            "bulk": TrafficClass("bulk", guaranteed_rate=30, parent="default"),
        }
    )
    assert validate_tree(good).outcome is ValidationOutcome.VALID

    unknown = ClassTree(
        classes={"video": TrafficClass("video", guaranteed_rate=60, parent="ghost")}
    )
    assert validate_tree(unknown).outcome is ValidationOutcome.UNKNOWN_PARENT

    cycle = ClassTree(
        classes={
            "a": TrafficClass("a", guaranteed_rate=10, parent="b"),
            "b": TrafficClass("b", guaranteed_rate=10, parent="a"),
        }
    )
    assert validate_tree(cycle).outcome is ValidationOutcome.CYCLE

    over = ClassTree(
        classes={
            "default": TrafficClass("default", guaranteed_rate=100, parent=None),
            "video": TrafficClass("video", guaranteed_rate=70, parent="default"),
            "bulk": TrafficClass("bulk", guaranteed_rate=50, parent="default"),
        }
    )
    assert validate_tree(over).outcome is ValidationOutcome.OVER_SUBSCRIBED

    # video (60) leaves 40 unused at default (100 - 60 - 30); bulk's own slack is 30
    # (30 - 0, it has no children) plus that same 40 percolating down from default.
    assert borrowable(good, "bulk") == 30 + (100 - 60 - 30)
    assert borrowable(good, "default") == 100 - 60 - 30

    print("[OK] classes.py")
