from __future__ import annotations

from dataclasses import dataclass, field

from .membership import GroupTable, leave

# Queries keep the set honest. A GroupTable only ever grows by an explicit join() -
# nothing in membership.py ever forgets a host on its own. Left alone, a host that
# quietly disappeared (crashed, unplugged, roamed off-link) would stay a "member"
# forever. IGMPv2's querier (RFC 2236, loosely: ~125s query interval, ~2x the max
# response time as the membership timeout) exists to test that assumption on a
# schedule instead of trusting it. This is the expiring-state family's third
# member in this course - dns/cache.py expires stale answers, dhcp/leases.py
# expires stale addresses, and here what expires is stale INTEREST: a host
# that stops answering queries is, for forwarding purposes, no longer there.

QUERY_INTERVAL = 125
MEMBERSHIP_TIMEOUT = 260


@dataclass
class MembershipState:
    """Per (group, host) pair, the clock time of the most recent report heard."""

    last_report_at: dict[tuple[str, str], int] = field(default_factory=dict)


def on_report(state: MembershipState, group: str, host: str, now: int) -> None:
    """A report - solicited by a query or sent unsolicited on join - resets the clock."""
    state.last_report_at[(group, host)] = now


def expire_silent(state: MembershipState, table: GroupTable, now: int) -> tuple[tuple[str, str], ...]:
    """Anyone who hasn't reported within MEMBERSHIP_TIMEOUT is presumed gone, not just quiet.

    This is the only place a membership disappears without an explicit leave(): it is
    the timeout side of the same expiring-dict shape as ResolverCache.lookup and
    LeaseTable.lookup_lease, except the check runs on a query cycle rather than at
    read time, because nothing here is "read" the way a cache entry is.
    """
    expired: list[tuple[str, str]] = []
    for (group, host), last_seen in list(state.last_report_at.items()):
        if now - last_seen >= MEMBERSHIP_TIMEOUT:
            expired.append((group, host))
            del state.last_report_at[(group, host)]
            leave(table, group, host)

    return tuple(expired)


def report_suppression(group_members_who_heard: tuple[str, ...]) -> str:
    """A query only needs one yes. Reports are multicast to the group address itself,
    so every other member hears the first answer and cancels its own timer - the
    switch (or router) only needed to learn "someone is still here," and it already
    has that. Modeling "pick the first responder" costs one message where a naive
    every-member-answers design would cost len(group_members_who_heard).
    """
    if not group_members_who_heard:
        raise ValueError("no member heard the query; nothing to suppress")

    return group_members_who_heard[0]
