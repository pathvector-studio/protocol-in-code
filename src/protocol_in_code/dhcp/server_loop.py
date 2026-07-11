from __future__ import annotations

from dataclasses import dataclass, field

from .discover import DhcpMessage, MessageType, MessageValidity, validate_message
from .leases import LeaseTable, grant_lease
from .offer import Offer, make_offer, offer_is_stale
from .pool import AddressPool, allocate, hold, next_free

DEFAULT_LEASE_SECONDS = 3600


@dataclass
class ToyDhcpServer:
    """Build the toy DHCP server loop: one server's state, wired to a full DORA exchange.

    Every DISCOVER/REQUEST that arrives runs through the same four modules this track
    built up to here: discover.py validates the message shape, pool.py finds and holds
    an address, offer.py decides whether a hold is still live, and leases.py is where a
    hold finally becomes a commitment. The server itself does none of that work directly
    - it only decides, per message, which module to call and in which order.
    """

    pool: AddressPool
    lease_table: LeaseTable = field(default_factory=LeaseTable)
    server_id: str = "server-1"
    clock: int = 0
    trace: list[str] = field(default_factory=list)
    _outstanding_offers: dict[str, Offer] = field(default_factory=dict)

    def tick(self, seconds: int) -> None:
        self.clock += seconds

    def on_message(self, msg: DhcpMessage) -> DhcpMessage | None:
        """Dispatch by message type: DISCOVER earns an OFFER, REQUEST earns an ACK or a NAK.

        A malformed message - one that fails validate_message from discover.py, such as
        a REQUEST with no server_id - is dropped before it reaches any state-changing
        code. The pool and the lease table only ever see messages that are shaped right.
        """
        validity = validate_message(msg)
        if validity is not MessageValidity.VALID:
            self.trace.append(f"{msg.message_type.value} from {msg.client_mac}: rejected ({validity.value})")
            return None

        if msg.message_type is MessageType.DISCOVER:
            return self._on_discover(msg)
        if msg.message_type is MessageType.REQUEST:
            return self._on_request(msg)

        self.trace.append(f"ignored: {msg.message_type.value}")
        return None

    def _on_discover(self, msg: DhcpMessage) -> DhcpMessage | None:
        """Discovery is shouting into the dark - this is the server's ear turned toward it.

        next_free walks the pool's visible candidate range and skips both allocated
        addresses and addresses still held by someone else's un-expired offer. If
        nothing is left, the DISCOVER is met with silence (POOL_EXHAUSTED): no OFFER,
        no NAK, nothing - a client that hears nothing back just times out and retries.
        """
        ip = next_free(self.pool, self.clock)
        if ip is None:
            self.trace.append(f"discover from {msg.client_mac}: pool exhausted, no offer made")
            return None

        hold(self.pool, ip, self.clock)
        offer = make_offer(ip, DEFAULT_LEASE_SECONDS, self.server_id, self.clock)
        self._outstanding_offers[msg.client_mac] = offer
        self.trace.append(
            f"discover from {msg.client_mac}: offering {ip}, hold expires at clock={offer.made_at}+OFFER_HOLD_SECONDS"
        )

        return DhcpMessage(
            message_type=MessageType.OFFER,
            transaction_id=msg.transaction_id,
            client_mac=msg.client_mac,
            offered_ip=ip,
            server_id=self.server_id,
        )

    def _on_request(self, msg: DhcpMessage) -> DhcpMessage:
        """A REQUEST is broadcast even though it names one server - every server hears it.

        This server only acts if the echoed server_id names it. A different server_id
        means some other server's offer was accepted, which is this server's cue to
        release its own hold quietly (it lost, without ever being told so directly).
        A NAK also covers the case where this server's own offer went stale while the
        client was still deciding: no free lunch just because a DISCOVER happened once.
        """
        if msg.server_id != self.server_id:
            stale_ip = self._outstanding_offers.pop(msg.client_mac, None)
            self.trace.append(f"request from {msg.client_mac}: server_id {msg.server_id!r} names another server, lost -> NAK")
            if stale_ip is not None:
                self.trace.append(f"  releasing our own hold on {stale_ip.ip}")
            return self._nak(msg)

        offer = self._outstanding_offers.get(msg.client_mac)
        if offer is None or offer_is_stale(offer, self.clock):
            self.trace.append(f"request from {msg.client_mac}: no live offer at clock={self.clock} -> NAK")
            return self._nak(msg)

        allocate(self.pool, offer.ip)
        grant_lease(self.lease_table, msg.client_mac, offer.ip, offer.lease_seconds, self.clock)
        self._outstanding_offers.pop(msg.client_mac, None)
        self.trace.append(f"request from {msg.client_mac}: granted {offer.ip} for {offer.lease_seconds}s -> ACK")

        return DhcpMessage(
            message_type=MessageType.ACK,
            transaction_id=msg.transaction_id,
            client_mac=msg.client_mac,
            offered_ip=offer.ip,
            server_id=self.server_id,
        )

    def _nak(self, msg: DhcpMessage) -> DhcpMessage:
        return DhcpMessage(
            message_type=MessageType.NAK,
            transaction_id=msg.transaction_id,
            client_mac=msg.client_mac,
            server_id=self.server_id,
        )


def run_dora(server: ToyDhcpServer, client_mac: str, transaction_id: int) -> tuple[DhcpMessage, ...]:
    """Walk the full Discover-Offer-Request-Ack exchange and hand back all four messages.

    Four steps, four messages, in order: DISCOVER (client, broadcast, knows nothing) ->
    OFFER (server, proposes an address and holds it) -> REQUEST (client, broadcast again,
    echoing the winning server_id and ip so every other server hears it lost) -> ACK
    (server, turns the hold into a real lease). The tuple this returns is exactly four
    long - that count is the point: DORA is not "however many messages it takes," it is
    a fixed four-step handshake, and a caller can assert len(result) == 4 to prove it.
    """
    discover = DhcpMessage(
        message_type=MessageType.DISCOVER,
        transaction_id=transaction_id,
        client_mac=client_mac,
    )
    offer_msg = server.on_message(discover)
    assert offer_msg is not None and offer_msg.message_type is MessageType.OFFER

    request = DhcpMessage(
        message_type=MessageType.REQUEST,
        transaction_id=transaction_id,
        client_mac=client_mac,
        server_id=offer_msg.server_id,
        requested_ip=offer_msg.offered_ip,
    )
    ack = server.on_message(request)
    assert ack is not None and ack.message_type is MessageType.ACK

    return (discover, offer_msg, request, ack)
