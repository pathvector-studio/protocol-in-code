from protocol_in_code.tcp.reassembly import DeliveryOutcome, ReassemblyBuffer, deliver


def main() -> None:
    print("Session 08 walkthrough: Out of order is not lost")
    print()

    buffer = ReassemblyBuffer(rcv_nxt=1000)

    in_order = deliver(buffer, 1000, 100)
    marker = "OK" if in_order.outcome is DeliveryOutcome.DELIVERED and buffer.rcv_nxt == 1100 else "NG"
    print(f"[{marker}] in-order segment delivers      -> {in_order.outcome.value} rcv_nxt={buffer.rcv_nxt}")

    gap = deliver(buffer, 1300, 100)
    marker = "OK" if gap.outcome is DeliveryOutcome.BUFFERED and buffer.rcv_nxt == 1100 and 1300 in buffer.segments else "NG"
    print(f"[{marker}] out-of-order segment buffers   -> {gap.outcome.value} rcv_nxt unmoved={buffer.rcv_nxt}")

    middle = deliver(buffer, 1200, 100)
    marker = "OK" if middle.outcome is DeliveryOutcome.BUFFERED and buffer.rcv_nxt == 1100 and len(buffer.segments) == 2 else "NG"
    print(f"[{marker}] second gap segment also waits  -> {middle.outcome.value} rcv_nxt unmoved={buffer.rcv_nxt} pending={sorted(buffer.segments)}")

    gap_filler = deliver(buffer, 1100, 100)
    marker = "OK" if (
        gap_filler.outcome is DeliveryOutcome.DELIVERED
        and gap_filler.delivered_len == 300
        and gap_filler.new_rcv_nxt == 1400
        and not buffer.segments
    ) else "NG"
    print(f"[{marker}] gap-filler drains the whole run -> {gap_filler.outcome.value} delivered_len={gap_filler.delivered_len} rcv_nxt={buffer.rcv_nxt}")

    stale = deliver(buffer, 1000, 100)
    marker = "OK" if stale.outcome is DeliveryOutcome.DUPLICATE and stale.delivered_len == 0 and buffer.rcv_nxt == 1400 else "NG"
    print(f"[{marker}] stale segment is a duplicate   -> {stale.outcome.value} rcv_nxt unchanged={buffer.rcv_nxt}")

    zero_len = deliver(buffer, 1400, 0)
    marker = "OK" if zero_len.outcome is DeliveryOutcome.DUPLICATE and buffer.rcv_nxt == 1400 else "NG"
    print(f"[{marker}] empty payload is not delivered -> {zero_len.outcome.value} rcv_nxt unchanged={buffer.rcv_nxt}")


if __name__ == "__main__":
    main()
