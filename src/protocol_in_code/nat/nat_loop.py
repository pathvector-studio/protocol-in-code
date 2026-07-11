from __future__ import annotations

from dataclasses import dataclass, field

from .five_tuple import FiveTuple, reply_tuple
from .ports import AllocationOutcome, PortAllocator, allocate_port
from .rewrite import Packet, apply_dnat, apply_snat
from .table import ConntrackTable, MatchDirection, NatEntry, insert, match
from .timeout import is_expired, sweep, touch


@dataclass
class ToyNatBox:
    """Build the toy NAT box: one public IP, one conntrack table, one port pool, wired to a clock."""

    public_ip: str
    table: ConntrackTable = field(default_factory=ConntrackTable)
    allocator: PortAllocator | None = None
    clock: int = 0
    trace: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.allocator is None:
            self.allocator = PortAllocator(public_ip=self.public_ip)

    def tick(self, seconds: int) -> None:
        self.clock += seconds
        # The allocator holds PUBLIC ports, so what gets reclaimed is
        # entry.translated.src_port — captured before sweep() removes the entries.
        reclaimable = {
            entry.translated.src_port
            for entry in self.table.entries.values()
            if is_expired(entry, self.clock)
        }
        expired = sweep(self.table, self.clock)
        for port in reclaimable:
            self.allocator.in_use.discard(port)
        for original in expired:
            self.trace.append(f"sweep at clock={self.clock}: expired {original}")

    def outbound(self, packet: Packet) -> Packet | None:
        """A private host's packet leaves: reuse an existing translation, or allocate a fresh one."""
        result = match(self.table, packet.tuple)

        if result.direction is MatchDirection.FORWARD:
            entry = touch(result.entry, self.clock)
            self.table.entries[entry.original] = entry
            self.table.entries[reply_tuple(entry.translated)] = entry
            translated = apply_snat(packet, entry.translated.src_ip, entry.translated.src_port)
            self.trace.append(f"outbound reuse: {packet.tuple} -> {translated.tuple}")
            return translated

        port = allocate_port(self.allocator)
        if port is None:
            self.trace.append(f"outbound drop: {packet.tuple} ({AllocationOutcome.POOL_EXHAUSTED.value})")
            return None

        translated_tuple = FiveTuple(
            protocol=packet.tuple.protocol,
            src_ip=self.public_ip,
            src_port=port,
            dst_ip=packet.tuple.dst_ip,
            dst_port=packet.tuple.dst_port,
        )
        entry = NatEntry(original=packet.tuple, translated=translated_tuple, created_at=self.clock)
        insert(self.table, entry)

        translated = apply_snat(packet, self.public_ip, port)
        self.trace.append(f"outbound new: {packet.tuple} -> {translated.tuple}")
        return translated

    def inbound(self, packet: Packet) -> Packet | None:
        """A packet arrives from the internet: un-NAT it back to the private host, or drop it as unsolicited.

        No match here does not mean an error - it means nobody inside asked for this.
        A NAT table with no entry for an inbound tuple behaves exactly like a firewall
        that default-denies everything it didn't see leave first.
        """
        result = match(self.table, packet.tuple)

        if result.direction is not MatchDirection.REVERSE:
            self.trace.append(f"inbound drop: {packet.tuple} (no entry, treated as unsolicited)")
            return None

        entry = touch(result.entry, self.clock)
        self.table.entries[entry.original] = entry
        self.table.entries[reply_tuple(entry.translated)] = entry

        restored = apply_dnat(packet, entry.original.src_ip, entry.original.src_port)
        self.trace.append(f"inbound un-nat: {packet.tuple} -> {restored.tuple}")
        return restored


def run_flow(box: ToyNatBox, private_tuple: FiveTuple) -> tuple[Packet | None, Packet | None]:
    """Drive one full round trip: private host sends out, the far side replies, the reply gets home."""
    outbound_packet = Packet(tuple=private_tuple, payload_note="request")
    translated = box.outbound(outbound_packet)
    if translated is None:
        return (None, None)

    reply_packet = Packet(tuple=reply_tuple(translated.tuple), payload_note="response")
    delivered = box.inbound(reply_packet)

    if delivered is not None:
        # The delivered packet is addressed TO the private host: its dst is the
        # private host's own src from private_tuple. It arrives as the reply
        # direction of private_tuple, not private_tuple itself - the far end's
        # address never changes, only the destination gets un-NATed.
        assert delivered.tuple == reply_tuple(private_tuple)
        assert delivered.tuple.dst_ip == private_tuple.src_ip
        assert delivered.tuple.dst_port == private_tuple.src_port
    box.trace.append(f"run_flow: private={private_tuple} delivered={delivered.tuple if delivered else None}")

    return (translated, delivered)
