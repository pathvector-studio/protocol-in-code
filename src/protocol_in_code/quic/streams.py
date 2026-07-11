from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# Deliberately the same shape as tcp/reassembly.py's ReassemblyBuffer (rcv offset + a
# dict of pending out-of-order pieces), but here it is PER STREAM. In TCP there is one
# sequence space for the whole connection, so a gap blocks the connection's only stream
# of bytes. In QUIC each stream has its own offset space, so a gap on one stream never
# blocks delivery on another: see the "stream 4 while stream 8 gapped" smoke test below.
#
# QUIC stream offsets are 62-bit and simply never wrap in practice, unlike TCP's 32-bit
# sequence numbers (see tcp/seqnum.py's seq_add/seq_lt ring arithmetic). So delivery here
# uses plain integer comparison instead of modular "before on the ring" logic.


class DeliveryOutcome(str, Enum):
    DELIVERED = "Delivered"
    BUFFERED = "Buffered"
    DUPLICATE = "Duplicate"


@dataclass(frozen=True)
class StreamDelivery:
    outcome: DeliveryOutcome
    delivered_len: int
    new_rcv_offset: int


@dataclass
class StreamBuffer:
    rcv_offset: int = 0
    pending: dict[int, int] = field(default_factory=dict)


@dataclass
class QuicConnection:
    """QUIC streams don't block each other: one buffer per stream, not one for the connection."""

    streams: dict[int, StreamBuffer] = field(default_factory=dict)


def _buffer_for(conn: QuicConnection, stream_id: int) -> StreamBuffer:
    return conn.streams.setdefault(stream_id, StreamBuffer())


def deliver(conn: QuicConnection, stream_id: int, offset: int, length: int) -> StreamDelivery:
    """A gap on this stream buffers only this stream; every other stream is unaffected."""
    buffer = _buffer_for(conn, stream_id)

    if length <= 0 or offset < buffer.rcv_offset:
        return StreamDelivery(DeliveryOutcome.DUPLICATE, 0, buffer.rcv_offset)

    if offset != buffer.rcv_offset:
        buffer.pending[offset] = length
        return StreamDelivery(DeliveryOutcome.BUFFERED, 0, buffer.rcv_offset)

    delivered_len = length
    buffer.rcv_offset += length

    while buffer.rcv_offset in buffer.pending:
        run_len = buffer.pending.pop(buffer.rcv_offset)
        delivered_len += run_len
        buffer.rcv_offset += run_len

    return StreamDelivery(DeliveryOutcome.DELIVERED, delivered_len, buffer.rcv_offset)


if __name__ == "__main__":
    conn = QuicConnection()

    # Stream 8 receives an out-of-order piece and gets stuck waiting for offset 0.
    gapped = deliver(conn, stream_id=8, offset=10, length=5)
    assert gapped.outcome is DeliveryOutcome.BUFFERED
    assert conn.streams[8].rcv_offset == 0

    # Stream 4 is untouched by stream 8's gap: it delivers in order, independently.
    delivered = deliver(conn, stream_id=4, offset=0, length=12)
    assert delivered.outcome is DeliveryOutcome.DELIVERED
    assert delivered.new_rcv_offset == 12
    assert conn.streams[8].rcv_offset == 0  # still gapped, proving isolation

    # Filling stream 8's gap now drains its buffered run.
    filled = deliver(conn, stream_id=8, offset=0, length=10)
    assert filled.outcome is DeliveryOutcome.DELIVERED
    assert filled.delivered_len == 15
    assert conn.streams[8].rcv_offset == 15

    duplicate = deliver(conn, stream_id=4, offset=0, length=12)
    assert duplicate.outcome is DeliveryOutcome.DUPLICATE

    print("[OK] streams.py")
