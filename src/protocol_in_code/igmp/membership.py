from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from ipaddress import ip_address, ip_network

MULTICAST_RANGE = ip_network("224.0.0.0/4")


class JoinOutcome(str, Enum):
    JOINED = "Joined"
    ALREADY_MEMBER = "AlreadyMember"
    MALFORMED_GROUP = "MalformedGroup"


@dataclass
class GroupTable:
    """Group membership is a set: a multicast group is nothing but its current members."""

    groups: dict[str, set[str]] = field(default_factory=dict)


def is_multicast_group(group: str) -> bool:
    """224.0.0.0/4 is the only address range IGMP is ever asked to talk about."""
    try:
        return ip_address(group) in MULTICAST_RANGE
    except ValueError:
        return False


def join(table: GroupTable, group: str, host: str) -> JoinOutcome:
    """Joining is set insertion - a host that's already a member changes nothing."""
    if not is_multicast_group(group):
        return JoinOutcome.MALFORMED_GROUP

    members = table.groups.setdefault(group, set())
    if host in members:
        return JoinOutcome.ALREADY_MEMBER

    members.add(host)
    return JoinOutcome.JOINED


def leave(table: GroupTable, group: str, host: str) -> None:
    """Leaving is set removal - an empty set is not a group anymore, so the key goes too.

    A silent hang-around empty entry would be a lie: it would say "this group exists"
    when nothing is listening. Deleting the key visibly is what lets anyone_interested
    stay a one-line dict lookup instead of a lookup plus an emptiness check.
    """
    members = table.groups.get(group)
    if members is None:
        return

    members.discard(host)
    if not members:
        del table.groups[group]


def anyone_interested(table: GroupTable, group: str) -> bool:
    """Multicast forwarding reduces to exactly this question: does the set exist and hold anyone?"""
    return bool(table.groups.get(group))


def groups_of(table: GroupTable, host: str) -> tuple[str, ...]:
    """The reverse view: every group whose member set currently contains this host."""
    return tuple(sorted(group for group, members in table.groups.items() if host in members))
