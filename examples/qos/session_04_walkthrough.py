from protocol_in_code.qos.classes import (
    ClassTree,
    TrafficClass,
    ValidationOutcome,
    borrowable,
    validate_tree,
)


def main() -> None:
    print("Session 04 walkthrough: Classes form a tree")
    print()

    good = ClassTree(
        classes={
            "default": TrafficClass("default", guaranteed_rate=100, parent=None),
            "video": TrafficClass("video", guaranteed_rate=60, parent="default"),
            "bulk": TrafficClass("bulk", guaranteed_rate=30, parent="default"),
        }
    )
    valid = validate_tree(good)
    marker = "OK" if valid.outcome is ValidationOutcome.VALID else "NG"
    print(f"[{marker}] 2-level tree, 60+30 under 100 -> {valid.outcome.value}")

    unknown = ClassTree(
        classes={"video": TrafficClass("video", guaranteed_rate=60, parent="ghost")}
    )
    unknown_result = validate_tree(unknown)
    marker = "OK" if unknown_result.outcome is ValidationOutcome.UNKNOWN_PARENT else "NG"
    print(f"[{marker}] parent 'ghost' does not exist -> {unknown_result.outcome.value}")

    cycle = ClassTree(
        classes={
            "a": TrafficClass("a", guaranteed_rate=10, parent="b"),
            "b": TrafficClass("b", guaranteed_rate=10, parent="a"),
        }
    )
    cycle_result = validate_tree(cycle)
    marker = "OK" if cycle_result.outcome is ValidationOutcome.CYCLE else "NG"
    print(f"[{marker}] a -> b -> a                  -> {cycle_result.outcome.value}")

    over = ClassTree(
        classes={
            "default": TrafficClass("default", guaranteed_rate=100, parent=None),
            "video": TrafficClass("video", guaranteed_rate=70, parent="default"),
            "bulk": TrafficClass("bulk", guaranteed_rate=50, parent="default"),
        }
    )
    over_result = validate_tree(over)
    marker = "OK" if over_result.outcome is ValidationOutcome.OVER_SUBSCRIBED else "NG"
    print(f"[{marker}] children claim 70+50=120 > 100 -> {over_result.outcome.value}")

    # bulk's own slack is 30 - 0 (no children of its own); default's own slack is
    # 100 - 60 - 30 = 10. borrowable(bulk) walks bulk then its parent default, so
    # 30 + 10 = 40.
    bulk_borrowable = borrowable(good, "bulk")
    marker = "OK" if bulk_borrowable == 40 else "NG"
    print(f"[{marker}] bulk: own 30 + default's 10   -> borrowable={bulk_borrowable}")


if __name__ == "__main__":
    main()
