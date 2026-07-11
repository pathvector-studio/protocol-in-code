from __future__ import annotations

from dataclasses import dataclass, field

from .cache import NeighborCache, NeighborState, confirm, lookup, start_resolution
from .gratuitous import ArpAnnouncement
from .pending import PendingQueue, enqueue, flush


@dataclass
class ToyArpNode:
    """Build the toy ARP responder loop: a host that resolves, queues, answers, and gleans."""

    name: str
    my_ip: str
    my_mac: str
    cache: NeighborCache = field(default_factory=NeighborCache)
    pending: PendingQueue = field(default_factory=PendingQueue)
    clock: int = 0
    trace: list[str] = field(default_factory=list)

    def tick(self, seconds: int) -> None:
        self.clock += seconds

    def send_to(self, ip: str, packet_label: str) -> str | None:
        """Deliver immediately if the mapping is usable; otherwise queue and go ask who has it."""
        result = lookup(self.cache, ip, self.clock)

        if result.state in (NeighborState.REACHABLE, NeighborState.STALE):
            self.trace.append(f"{self.name}: send {packet_label} to {ip} via {result.mac} ({result.state.value})")
            return result.mac

        if result.state is None:
            start_resolution(self.cache, ip, self.clock)
        outcome = enqueue(self.pending, ip, packet_label)
        self.trace.append(f"{self.name}: queue {packet_label} for {ip} ({outcome.value}); who-has {ip}?")
        return None

    def on_request(self, ip_asked: str, from_ip: str, from_mac: str) -> ArpAnnouncement | None:
        """Answer a who-has for my own IP, and glean the asker's mapping from the request itself."""
        confirm(self.cache, from_ip, from_mac, self.clock)
        self.trace.append(f"{self.name}: glean {from_ip} -> {from_mac} from the request")

        if ip_asked != self.my_ip:
            return None

        self.trace.append(f"{self.name}: is-at {self.my_mac} for {ip_asked}")
        return ArpAnnouncement(ip=ip_asked, mac=self.my_mac, is_reply_to_us=True)

    def on_reply(self, announcement: ArpAnnouncement) -> tuple[str, ...]:
        """A reply arrives: trust it, confirm the entry, and release everything that was waiting."""
        confirm(self.cache, announcement.ip, announcement.mac, self.clock)
        delivered = flush(self.pending, announcement.ip)
        self.trace.append(
            f"{self.name}: confirmed {announcement.ip} -> {announcement.mac}, delivering {delivered}"
        )
        return delivered


def run_resolution(a: ToyArpNode, b: ToyArpNode, packet_label: str) -> tuple[str, ...]:
    """Walk the full exchange: A queues and asks, B answers and gleans, A flushes and delivers."""
    mac = a.send_to(b.my_ip, packet_label)
    if mac is not None:
        return (packet_label,)

    announcement = b.on_request(ip_asked=b.my_ip, from_ip=a.my_ip, from_mac=a.my_mac)
    if announcement is None:
        return ()

    return a.on_reply(announcement)
