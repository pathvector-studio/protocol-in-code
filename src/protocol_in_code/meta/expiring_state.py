"""The expiring dict, five times.

DNS cache entries, TLS session tickets, DHCP leases, NAT conntrack entries,
and IGMP membership interest are five different nouns wearing one costume:
a dict keyed by identity, a frozen value stamped with the time it was
created, and a read (or sweep) that compares `now` against `stamp + lifetime`
to decide whether the value still counts. This file runs all five real
implementations back to back, before and after their own expiry, and
records what each one actually returned - not a paraphrase of the shape,
the shape itself, five times over.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..dhcp.leases import LeaseOutcome, LeaseTable, grant_lease, lookup_lease
from ..dns.cache import CacheOutcome, ResolverCache, lookup as dns_lookup, store as dns_store
from ..dns.query import DNSQuestion
from ..igmp.membership import GroupTable, join as igmp_join
from ..igmp.querier import MembershipState, expire_silent, on_report
from ..nat.five_tuple import FiveTuple
from ..nat.table import ConntrackTable, NatEntry, insert as nat_insert
from ..nat.timeout import sweep as nat_sweep
from ..tls.resumption import TicketOutcome, TicketStore, issue_ticket, lookup_ticket


@dataclass(frozen=True)
class ExpiryDemo:
    protocol: str
    what_expires: str
    outcome_name: str


def demonstrate_all(now_gap: int) -> tuple[ExpiryDemo, ...]:
    """Run each real expiring store through insert -> hit -> advance clock -> expire.

    `now_gap` is the number of clock ticks each stanza advances past the
    thing's own lifetime, so every store is asked to expire by the same
    margin even though their native lifetimes (TTL, ticket lifetime, lease
    duration, conntrack timeout, membership timeout) are all different sizes.
    """
    rows: list[ExpiryDemo] = []

    # --- DNS: a cached answer, keyed by (name, type, class) -----------------
    dns_cache = ResolverCache()
    question = DNSQuestion(qname="example.com", qtype="A", qclass="IN")
    dns_store(dns_cache, question, ("93.184.216.34",), ttl=30, now=0)
    hit = dns_lookup(dns_cache, question, now=10)
    rows.append(ExpiryDemo("dns", "cached answer", hit.outcome.value))
    expired = dns_lookup(dns_cache, question, now=30 + now_gap)
    rows.append(ExpiryDemo("dns", "cached answer", expired.outcome.value))
    assert expired.outcome is CacheOutcome.EXPIRED

    # --- TLS: a session resumption ticket, keyed by server name -------------
    ticket_store = TicketStore()
    issue_ticket(ticket_store, "example.com", "master-secret", "TLS_AES_128_GCM_SHA256", lifetime=3600, now=0)
    hit = lookup_ticket(ticket_store, "example.com", now=100)
    rows.append(ExpiryDemo("tls", "session ticket", hit.outcome.value))
    expired = lookup_ticket(ticket_store, "example.com", now=3600 + now_gap)
    rows.append(ExpiryDemo("tls", "session ticket", expired.outcome.value))
    assert expired.outcome is TicketOutcome.EXPIRED

    # --- DHCP: an address lease, keyed by MAC address ------------------------
    lease_table = LeaseTable()
    grant_lease(lease_table, "aa:bb:cc:dd:ee:ff", "10.0.0.5", duration=3600, now=0)
    hit = lookup_lease(lease_table, "aa:bb:cc:dd:ee:ff", now=1000)
    rows.append(ExpiryDemo("dhcp", "address lease", hit.outcome.value))
    expired = lookup_lease(lease_table, "aa:bb:cc:dd:ee:ff", now=3600 + now_gap)
    rows.append(ExpiryDemo("dhcp", "address lease", expired.outcome.value))
    assert expired.outcome is LeaseOutcome.EXPIRED

    # --- NAT: a conntrack entry, keyed by five-tuple -------------------------
    conntrack = ConntrackTable()
    original = FiveTuple(protocol="udp", src_ip="10.0.0.5", src_port=4000, dst_ip="93.184.216.34", dst_port=53)
    translated = FiveTuple(protocol="udp", src_ip="203.0.113.1", src_port=40000, dst_ip="93.184.216.34", dst_port=53)
    nat_insert(conntrack, NatEntry(original=original, translated=translated, created_at=0))
    removed_before = nat_sweep(conntrack, now=10)
    rows.append(ExpiryDemo("nat", "conntrack entry", "Hit" if not removed_before else "Expired"))
    removed_after = nat_sweep(conntrack, now=30 + now_gap)
    rows.append(ExpiryDemo("nat", "conntrack entry", "Expired" if removed_after else "Hit"))
    assert original in removed_after

    # --- IGMP: a (group, host) membership interest, keyed by that pair ------
    group_table = GroupTable()
    igmp_membership = MembershipState()
    igmp_join(group_table, "239.1.1.1", "host-a")
    on_report(igmp_membership, "239.1.1.1", "host-a", now=0)
    expired_before = expire_silent(igmp_membership, group_table, now=10)
    rows.append(ExpiryDemo("igmp", "membership interest", "Hit" if not expired_before else "Expired"))
    expired_after = expire_silent(igmp_membership, group_table, now=260 + now_gap)
    rows.append(ExpiryDemo("igmp", "membership interest", "Expired" if expired_after else "Hit"))
    assert ("239.1.1.1", "host-a") in expired_after

    return tuple(rows)


def common_shape() -> tuple[str, ...]:
    """The four steps every expiring store in this course shares.

    ARP (arp/cache.py) is the one exception worth cross-referencing here: a
    REACHABLE neighbor entry that outlives its window does not get deleted
    on the fourth step, it DEGRADES to STALE in place. Every store above
    forgets on expiry; ARP just stops trusting.
    """
    return (
        "keyed store",
        "insert stamps a time",
        "read compares now against stamp+lifetime",
        "expiry deletes (or degrades - see arp/cache.py's REACHABLE -> STALE, the one exception)",
    )
