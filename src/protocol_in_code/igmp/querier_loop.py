from __future__ import annotations

from dataclasses import dataclass, field

from .membership import GroupTable, join
from .querier import MEMBERSHIP_TIMEOUT, QUERY_INTERVAL, MembershipState, expire_silent, on_report, report_suppression
from .snooping import SnoopingTable, forward_ports, observe_query, observe_report

QUERIER_PORT = 0


@dataclass
class ToyQuerier:
    """Build the toy querier loop: one router's membership picture, wired to the query cycle."""

    table: GroupTable = field(default_factory=GroupTable)
    state: MembershipState = field(default_factory=MembershipState)
    clock: int = 0
    trace: list[str] = field(default_factory=list)

    def tick(self, seconds: int) -> None:
        self.clock += seconds

    def general_query(self) -> None:
        self.trace.append(f"querier: general query sent at clock={self.clock}")

    def receive_report(self, group: str, host: str) -> None:
        join(self.table, group, host)
        on_report(self.state, group, host, self.clock)
        self.trace.append(f"querier: report {host} -> {group} at clock={self.clock}")

    def expire(self) -> tuple[tuple[str, str], ...]:
        """Run the timeout side of the expiring-state shape and trace exactly who fell out."""
        expired = expire_silent(self.state, self.table, self.clock)
        for group, host in expired:
            self.trace.append(
                f"querier: {host} silent since before clock={self.clock - MEMBERSHIP_TIMEOUT}, expired from {group}"
            )
        return expired


@dataclass
class ToySnoopingSwitch:
    """Build the toy snooping switch: overhears the same reports and queries the querier sees."""

    table: SnoopingTable = field(default_factory=SnoopingTable)
    trace: list[str] = field(default_factory=list)

    def hear_query(self, port: int) -> None:
        observe_query(self.table, port)
        self.trace.append(f"switch: query overheard on port {port}, querier_port={port}")

    def hear_report(self, port: int, group: str) -> None:
        observe_report(self.table, port, group)
        self.trace.append(f"switch: report overheard on port {port} for {group}")

    def prune(self, group: str, host_port: int) -> None:
        """Mirror an expiry the querier reported: the switch's own copy of interest shrinks too."""
        self.table.port_groups.get(host_port, set()).discard(group)
        self.trace.append(f"switch: port {host_port} pruned from {group} (querier expired the member behind it)")

    def forwarding_set(self, group: str, all_ports: tuple[int, ...]) -> tuple[int, ...]:
        return forward_ports(self.table, group, all_ports)


def run_query_cycle(
    querier: ToyQuerier,
    switch: ToySnoopingSwitch,
    hosts: dict[str, tuple[str, ...]],
    silent_hosts: tuple[str, ...],
) -> None:
    """Walk one full query cycle and let the trace show a forwarding set shrink because someone went quiet.

    `hosts` maps a host name to (port, group): the switch port it sits behind and the
    group it belongs to. The steps, in order: (1) the router's general query goes out
    and the switch overhears it on the querier's port; (2) every host reports its group
    at least once, so the switch's forwarding table has a real baseline and the BEFORE
    snapshot is taken - when two hosts share a group, only the first is modeled as
    answering and report_suppression names why the rest can safely stay quiet; (3) a
    second query cycle begins, but this time silent_hosts do not answer; (4) the clock
    advances past MEMBERSHIP_TIMEOUT with no report from them; (5) expire_silent removes
    exactly those hosts from the querier's table, and the switch mirrors each expiry by
    pruning the matching port; (6) the AFTER snapshot is taken - smaller than BEFORE,
    not because anyone explicitly left, but because nobody spoke up on the second query.
    """
    querier.general_query()
    switch.hear_query(QUERIER_PORT)

    members_by_group: dict[str, list[str]] = {}
    for host, (_port, group) in hosts.items():
        members_by_group.setdefault(group, []).append(host)

    all_ports = tuple(sorted({QUERIER_PORT} | {port for port, _group in hosts.values()}))

    # First query cycle: everyone answers, so the switch builds a real baseline.
    for group, members in members_by_group.items():
        if len(members) > 1:
            responder = report_suppression(tuple(members))
            querier.trace.append(
                f"querier: {group} has {len(members)} interested members {tuple(members)}, "
                f"suppression -> only {responder} reports, {len(members) - 1} message(s) saved"
            )
        else:
            responder = members[0]

        port, _group = hosts[responder]
        querier.receive_report(group, responder)
        switch.hear_report(port, group)

    # Watch whichever group actually has a silent member - that's the group whose
    # forwarding set has something to lose. Falls back to the first group if nobody
    # in this cycle is silent, so the trace still runs (with an unchanged BEFORE/AFTER).
    watched_group = next(
        (group for group, members in members_by_group.items() if any(h in silent_hosts for h in members)),
        next(iter(members_by_group), None),
    )
    if watched_group is not None:
        before = switch.forwarding_set(watched_group, all_ports)
        querier.trace.append(f"forwarding[{watched_group}] BEFORE expiry: ports={before}")

    # Second query cycle: only the non-silent hosts answer this time.
    querier.tick(QUERY_INTERVAL)
    querier.general_query()
    switch.hear_query(QUERIER_PORT)

    for group, members in members_by_group.items():
        answering = tuple(host for host in members if host not in silent_hosts)
        if not answering:
            continue
        responder = report_suppression(answering) if len(answering) > 1 else answering[0]
        port, _group = hosts[responder]
        querier.receive_report(group, responder)
        switch.hear_report(port, group)

    # Advance to just past MEMBERSHIP_TIMEOUT measured from the *first* cycle's reports
    # (clock=0): long enough that a host silent since then is stale, but short enough
    # that a host which answered on the second cycle (clock=QUERY_INTERVAL) is still
    # fresh. This is exactly the gap IGMPv2's numbers are chosen to leave open.
    querier.clock = MEMBERSHIP_TIMEOUT
    querier.trace.append(f"querier: clock advanced to {querier.clock} (past MEMBERSHIP_TIMEOUT since the first cycle)")
    expired = querier.expire()

    for group, host in expired:
        port, _group = hosts[host]
        switch.prune(group, port)

    if watched_group is not None:
        after = switch.forwarding_set(watched_group, all_ports)
        querier.trace.append(f"forwarding[{watched_group}] AFTER expiry:  ports={after}")

        if len(after) < len(before):
            querier.trace.append(
                f"forwarding[{watched_group}] shrank: someone stopped answering, so the switch stopped forwarding to them"
            )
