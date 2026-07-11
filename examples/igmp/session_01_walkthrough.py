from protocol_in_code.igmp.membership import (
    GroupTable,
    JoinOutcome,
    anyone_interested,
    groups_of,
    join,
    leave,
)


def main() -> None:
    print("Session 01 walkthrough: Group membership is a set")
    print()

    table = GroupTable()

    first_join = join(table, "224.0.1.5", "host-a")
    marker = "OK" if first_join is JoinOutcome.JOINED else "NG"
    print(f"[{marker}] host-a joins 224.0.1.5      -> {first_join.value}")

    second_join = join(table, "224.0.1.5", "host-a")
    marker = "OK" if second_join is JoinOutcome.ALREADY_MEMBER else "NG"
    print(f"[{marker}] host-a joins again           -> {second_join.value}")

    unicast_join = join(table, "10.0.0.9", "host-a")
    marker = "OK" if unicast_join is JoinOutcome.MALFORMED_GROUP else "NG"
    print(f"[{marker}] host-a joins a unicast addr  -> {unicast_join.value}")

    join(table, "224.0.1.5", "host-b")
    leave(table, "224.0.1.5", "host-a")
    leave(table, "224.0.1.5", "host-b")
    marker = "OK" if "224.0.1.5" not in table.groups else "NG"
    print(f"[{marker}] last member leaves           -> key deleted, groups={table.groups}")

    marker = "OK" if not anyone_interested(table, "224.0.1.5") else "NG"
    print(f"[{marker}] anyone_interested after empty -> {anyone_interested(table, '224.0.1.5')}")

    join(table, "224.0.1.5", "host-c")
    marker = "OK" if anyone_interested(table, "224.0.1.5") else "NG"
    print(f"[{marker}] anyone_interested after join  -> {anyone_interested(table, '224.0.1.5')}")

    join(table, "224.0.2.9", "host-c")
    marker = "OK" if groups_of(table, "host-c") == ("224.0.1.5", "224.0.2.9") else "NG"
    print(f"[{marker}] groups_of host-c              -> {groups_of(table, 'host-c')}")


if __name__ == "__main__":
    main()
