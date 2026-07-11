from protocol_in_code.igmp.snooping import (
    SnoopingTable,
    forward_ports,
    observe_query,
    observe_report,
    unknown_group_behavior,
)


def main() -> None:
    print("Session 03 walkthrough: Snooping reads someone else's mail")
    print()

    table = SnoopingTable()
    all_ports = (0, 1, 2, 3)

    observe_query(table, port=0)
    marker = "OK" if table.querier_port == 0 else "NG"
    print(f"[{marker}] observe_query on port 0        -> querier_port={table.querier_port}")

    observe_report(table, port=1, group="224.0.1.5")
    observe_report(table, port=3, group="224.0.1.5")
    marker = "OK" if table.port_groups == {1: {"224.0.1.5"}, 3: {"224.0.1.5"}} else "NG"
    print(f"[{marker}] port->groups built from reports -> {table.port_groups}")

    pruned = forward_ports(table, "224.0.1.5", all_ports)
    marker = "OK" if pruned == (0, 1, 3) else "NG"
    print(f"[{marker}] forward_ports pruned not flooded -> ports={pruned}")

    flooded = unknown_group_behavior(all_ports)
    marker = "OK" if flooded == all_ports else "NG"
    print(f"[{marker}] unknown group floods all ports  -> ports={flooded}")

    unknown_forward = forward_ports(table, "224.0.9.9", all_ports)
    marker = "OK" if unknown_forward == (0,) else "NG"
    print(f"[{marker}] no members, querier port only   -> ports={unknown_forward}")

    marker = "OK" if 0 in pruned and 0 in unknown_forward else "NG"
    print(f"[{marker}] querier port always included     -> port 0 present in both results above")


if __name__ == "__main__":
    main()
