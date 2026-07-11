from protocol_in_code.rip.update import RoutingTable, UpdateOutcome, process_advertisement


def main() -> None:
    print("Session 02 walkthrough: Bellman-Ford is a for loop")
    print()

    table = RoutingTable()

    new = process_advertisement(table, "N1", (("10.0.0.0/24", 3),))
    stored = table.routes["10.0.0.0/24"]
    marker = "OK" if new == (UpdateOutcome.ADOPTED_NEW,) and stored.metric == 4 else "NG"
    print(f"[{marker}] N1 advertises 3            -> {new[0].value}, stored metric = {stored.metric} (3 + 1)")

    better_route = process_advertisement(table, "N2", (("10.0.0.0/24", 1),))
    stored = table.routes["10.0.0.0/24"]
    marker = "OK" if better_route == (UpdateOutcome.ADOPTED_BETTER,) and stored.metric == 2 else "NG"
    print(f"[{marker}] N2 advertises 1, beats 4    -> {better_route[0].value}, stored metric = {stored.metric}")

    ignored = process_advertisement(table, "N1", (("10.0.0.0/24", 5),))
    stored = table.routes["10.0.0.0/24"]
    marker = "OK" if ignored == (UpdateOutcome.IGNORED_WORSE,) and stored.metric == 2 else "NG"
    print(f"[{marker}] N1 (not our source) advertises 5 -> {ignored[0].value}, stored metric stays {stored.metric}")

    same_source_worse = process_advertisement(table, "N2", (("10.0.0.0/24", 10),))
    stored = table.routes["10.0.0.0/24"]
    marker = "OK" if same_source_worse == (UpdateOutcome.UPDATED_SAME_SOURCE,) and stored.metric == 11 else "NG"
    print(f"[{marker}] believe your own source     -> {same_source_worse[0].value}, stored metric = {stored.metric} (worse, adopted anyway)")

    clamped = process_advertisement(table, "N3", (("20.0.0.0/24", 20),))
    stored = table.routes["20.0.0.0/24"]
    marker = "OK" if clamped == (UpdateOutcome.ADOPTED_NEW,) and stored.metric == 16 else "NG"
    print(f"[{marker}] N3 advertises 20 (20 + 1 > 16) -> {clamped[0].value}, stored metric clamped to {stored.metric}")


if __name__ == "__main__":
    main()
