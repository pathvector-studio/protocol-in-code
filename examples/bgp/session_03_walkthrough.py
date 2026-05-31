from protocol_in_code.bgp.best_path import PathCandidate, select_best_path


def first_reason(candidate: PathCandidate, current: PathCandidate) -> str:
    if candidate.weight != current.weight:
        return "higher weight wins"
    if candidate.local_pref != current.local_pref:
        return "higher local_pref wins"
    if len(candidate.as_path) != len(current.as_path):
        return "shorter AS_PATH wins"
    if candidate.origin_type != current.origin_type:
        return "lower origin_type wins"
    return "next_hop tiebreaker wins"


def describe(path: PathCandidate) -> str:
    return (
        f"next_hop={path.next_hop}, weight={path.weight}, "
        f"local_pref={path.local_pref}, as_path_len={len(path.as_path)}, "
        f"origin_type={path.origin_type}"
    )


def main() -> None:
    scenarios = (
        (
            "weight decides first",
            [
                PathCandidate(prefix="203.0.113.0/24", next_hop="10.0.0.1", weight=200, local_pref=100, as_path=(65001, 65002)),
                PathCandidate(prefix="203.0.113.0/24", next_hop="10.0.0.2", weight=100, local_pref=300, as_path=(65009,)),
            ],
        ),
        (
            "local_pref decides after equal weight",
            [
                PathCandidate(prefix="203.0.113.0/24", next_hop="10.0.0.1", weight=100, local_pref=100, as_path=(65001, 65002)),
                PathCandidate(prefix="203.0.113.0/24", next_hop="10.0.0.2", weight=100, local_pref=200, as_path=(65009, 65010, 65011)),
            ],
        ),
        (
            "AS path length decides after earlier ties",
            [
                PathCandidate(prefix="203.0.113.0/24", next_hop="10.0.0.1", weight=100, local_pref=100, as_path=(65001, 65002, 65003)),
                PathCandidate(prefix="203.0.113.0/24", next_hop="10.0.0.2", weight=100, local_pref=100, as_path=(65009,)),
            ],
        ),
        (
            "origin type decides after AS path tie",
            [
                PathCandidate(prefix="203.0.113.0/24", next_hop="10.0.0.1", weight=100, local_pref=100, as_path=(65001,), origin_type=1),
                PathCandidate(prefix="203.0.113.0/24", next_hop="10.0.0.2", weight=100, local_pref=100, as_path=(65009,), origin_type=0),
            ],
        ),
    )

    print("Session 03 walkthrough: Best path selection as if statements")
    print()
    for title, paths in scenarios:
        best = select_best_path(paths)
        other = paths[0] if best is paths[1] else paths[1]
        reason = first_reason(best, other)
        print(f"- {title}")
        print(f"  winner: {describe(best)}")
        print(f"  loser : {describe(other)}")
        print(f"  first deciding reason: {reason}")
        print()


if __name__ == "__main__":
    main()
