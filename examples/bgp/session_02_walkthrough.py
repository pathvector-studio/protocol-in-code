from protocol_in_code.bgp.update import BGPUpdate, PathAttributes, RoutingTable, apply_update_message


def snapshot(table: RoutingTable) -> dict[str, list[dict[str, object]]]:
    view: dict[str, list[dict[str, object]]] = {}
    for prefix, paths in sorted(table.paths_by_prefix.items()):
        view[prefix] = [
            {
                "next_hop": path.next_hop,
                "as_path": list(path.as_path),
                "origin": path.origin,
                "local_pref": path.local_pref,
            }
            for path in paths
        ]
    return view


def main() -> None:
    table = RoutingTable()
    attrs_a = PathAttributes(next_hop="192.0.2.1", as_path=(65001,), origin="igp")
    attrs_b = PathAttributes(next_hop="192.0.2.2", as_path=(65002, 65009), origin="egp", local_pref=200)

    scenarios = (
        (
            "announce first path",
            BGPUpdate(nlri=("203.0.113.0/24",), path_attributes=attrs_a),
        ),
        (
            "announce second path for same prefix",
            BGPUpdate(nlri=("203.0.113.0/24",), path_attributes=attrs_b),
        ),
        (
            "withdraw existing prefix",
            BGPUpdate(withdrawn_routes=("203.0.113.0/24",)),
        ),
        (
            "announce two prefixes at once",
            BGPUpdate(
                nlri=("198.51.100.0/24", "198.51.101.0/24"),
                path_attributes=attrs_a,
            ),
        ),
        (
            "withdraw one prefix and add another in one UPDATE",
            BGPUpdate(
                withdrawn_routes=("198.51.100.0/24",),
                nlri=("203.0.113.0/24",),
                path_attributes=attrs_b,
            ),
        ),
    )

    print("Session 02 walkthrough: How UPDATE changes state")
    print()
    for step, update in scenarios:
        apply_update_message(table, update)
        print(f"- {step}")
        print(snapshot(table))
        print()


if __name__ == "__main__":
    main()
