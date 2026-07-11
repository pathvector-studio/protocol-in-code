from __future__ import annotations

from dataclasses import dataclass, field

# Snooping reads someone else's mail. IGMP is a layer-3 protocol between hosts and
# routers; a switch has no business parsing it. But a switch that ignores IGMP has
# only one honest option for a multicast frame - flood every port - because it has
# no layer-3 concept of "who wants this." IGMP snooping is a deliberate layering
# violation: the switch eavesdrops on reports and queries it was never addressed to,
# purely so it can prune. Nothing here changes IGMP; it only lets the switch build
# its own, lesser copy of the membership picture that membership.py already models.


@dataclass
class SnoopingTable:
    """Per switch port, the multicast groups seen requested there, plus which port the querier is on."""

    port_groups: dict[int, set[str]] = field(default_factory=dict)
    querier_port: int | None = None


def observe_report(table: SnoopingTable, port: int, group: str) -> None:
    """A report overheard on a port is the switch's only evidence that port wants the group."""
    table.port_groups.setdefault(port, set()).add(group)


def observe_query(table: SnoopingTable, port: int) -> None:
    """A query can only have come from a router - that's where the querier lives."""
    table.querier_port = port


def forward_ports(table: SnoopingTable, group: str, all_ports: tuple[int, ...]) -> tuple[int, ...]:
    """Prune to member ports plus the querier port - not everyone, and not "just members" either.

    Member ports get the frame because they asked. The querier port gets it too, even
    if the switch never saw a report there, because the router may have its own
    downstream members the switch can't see, and because the router needs the traffic
    to route it elsewhere in the first place.
    """
    return tuple(
        port
        for port in all_ports
        if group in table.port_groups.get(port, set()) or port == table.querier_port
    )


def unknown_group_behavior(all_ports: tuple[int, ...]) -> tuple[int, ...]:
    """A group the switch has never heard reported gets flooded - the honest default.

    Snooping only narrows forwarding for groups it has positive evidence about. Silence
    is not evidence of absence: a member could be there and simply not yet reported
    (or the switch could have missed it), so the safe fallback is to behave exactly
    like a switch with no snooping at all.
    """
    return all_ports
