from protocol_in_code.quic.streams import DeliveryOutcome, QuicConnection, deliver


def main() -> None:
    print("Session 08 walkthrough: QUIC streams don't block each other")
    print()

    conn = QuicConnection()

    in_order = deliver(conn, stream_id=4, offset=0, length=10)
    marker = "OK" if in_order.outcome is DeliveryOutcome.DELIVERED and in_order.new_rcv_offset == 10 else "NG"
    print(f"[{marker}] stream 4 in-order arrival        -> {in_order.outcome.value} rcv_offset={in_order.new_rcv_offset}")

    gapped = deliver(conn, stream_id=8, offset=10, length=5)
    marker = "OK" if gapped.outcome is DeliveryOutcome.BUFFERED and conn.streams[8].rcv_offset == 0 else "NG"
    print(f"[{marker}] stream 8 gapped arrival           -> {gapped.outcome.value} rcv_offset={conn.streams[8].rcv_offset}")

    unblocked = deliver(conn, stream_id=4, offset=10, length=7)
    marker = "OK" if unblocked.outcome is DeliveryOutcome.DELIVERED and conn.streams[8].rcv_offset == 0 else "NG"
    print(f"[{marker}] stream 4 delivers while 8 is gapped -> {unblocked.outcome.value}  <- headline: one stream's gap never blocks another")

    fill_gap = deliver(conn, stream_id=8, offset=0, length=10)
    marker = "OK" if fill_gap.outcome is DeliveryOutcome.DELIVERED and fill_gap.delivered_len == 15 else "NG"
    print(f"[{marker}] stream 8 gap-filling arrival      -> {fill_gap.outcome.value} delivered_len={fill_gap.delivered_len}")

    stale = deliver(conn, stream_id=4, offset=0, length=10)
    marker = "OK" if stale.outcome is DeliveryOutcome.DUPLICATE else "NG"
    print(f"[{marker}] stream 4 stale offset             -> {stale.outcome.value}")

    zero_len = deliver(conn, stream_id=4, offset=17, length=0)
    marker = "OK" if zero_len.outcome is DeliveryOutcome.DUPLICATE else "NG"
    print(f"[{marker}] stream 4 zero-length arrival      -> {zero_len.outcome.value}")


if __name__ == "__main__":
    main()
