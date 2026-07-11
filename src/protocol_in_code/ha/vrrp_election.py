"""The highest priority speaks.

VRRP (RFC 5798) elects a master to answer for a shared virtual IP the same
way OSPF elects a designated router (see ospf/dr_election.py) and RIP picks
a preferred route (see rip/route.py better()): rank every candidate by a
comparison key and take the max. This is the third appearance of
election-by-comparison in this course - OSPF compares (priority, router_id),
RIP compares a single metric, and VRRP compares (priority, primary_ip). Same
shape, protocol-specific rulebook.
"""

from __future__ import annotations

from dataclasses import dataclass

PRIORITY_OWNER = 255
"""RFC 5798 reserves 255 for the router that owns the virtual IP address itself.
An address owner always outranks every other candidate, no matter what priority
they were configured with - it is not "high priority," it is authoritative."""


def _ip_key(ip: str) -> tuple[int, ...]:
    return tuple(int(part) for part in ip.split("."))


@dataclass(frozen=True)
class VrrpRouter:
    name: str
    priority: int
    primary_ip: str


def elect(routers: tuple[VrrpRouter, ...]) -> VrrpRouter:
    """Highest priority wins; a tied priority is broken by the higher primary IP address.

    RFC 5798's tiebreak is deliberately arbitrary-looking but total: every
    router in a VRRP group has a distinct primary IP, so (priority, ip) always
    picks exactly one master, even if every router was configured with the
    same priority.
    """
    return max(routers, key=lambda router: (router.priority, _ip_key(router.primary_ip)))


def should_preempt(current_master: VrrpRouter, candidate: VrrpRouter, preempt_enabled: bool) -> bool:
    """Does a newly-heard-from `candidate` take over from `current_master`?

    Preemption is a tradeoff, not a correctness question: with preemption on,
    the best-priority router always ends up mastering, so failback is fast and
    predictable after a flaky router recovers. With preemption off, a returning
    high-priority router stays quiet as backup, trading best-router placement
    for less churn on links where flapping is expensive.
    """
    if not preempt_enabled:
        return False
    return candidate.priority > current_master.priority
