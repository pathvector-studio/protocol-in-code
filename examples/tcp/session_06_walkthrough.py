from protocol_in_code.tcp.fast_retransmit import AckSignal, AckTracker, DUP_ACK_THRESHOLD, on_ack


def main() -> None:
    print("Session 06 walkthrough: Three duplicates mean loss")
    print()

    tracker = AckTracker()

    first = on_ack(tracker, 1000)
    marker = "OK" if first is AckSignal.NEW_DATA_ACKED and tracker.dup_count == 0 else "NG"
    print(f"[{marker}] first ack for 1000            -> {first.value} dup_count={tracker.dup_count}")

    dup1 = on_ack(tracker, 1000)
    marker = "OK" if dup1 is AckSignal.DUPLICATE and tracker.dup_count == 1 else "NG"
    print(f"[{marker}] repeat #1                     -> {dup1.value} dup_count={tracker.dup_count}")

    dup2 = on_ack(tracker, 1000)
    marker = "OK" if dup2 is AckSignal.DUPLICATE and tracker.dup_count == 2 else "NG"
    print(f"[{marker}] repeat #2                     -> {dup2.value} dup_count={tracker.dup_count}")

    dup3 = on_ack(tracker, 1000)
    marker = "OK" if dup3 is AckSignal.FAST_RETRANSMIT and tracker.dup_count == DUP_ACK_THRESHOLD else "NG"
    print(f"[{marker}] repeat #3 hits the threshold  -> {dup3.value} dup_count={tracker.dup_count}")

    dup4 = on_ack(tracker, 1000)
    marker = "OK" if dup4 is AckSignal.DUPLICATE and tracker.dup_count == 4 else "NG"
    print(f"[{marker}] repeat #4 is not a re-trigger -> {dup4.value} dup_count={tracker.dup_count}")

    new_data = on_ack(tracker, 2000)
    marker = "OK" if new_data is AckSignal.NEW_DATA_ACKED and tracker.dup_count == 0 and tracker.last_ack == 2000 else "NG"
    print(f"[{marker}] new data resets the counter   -> {new_data.value} dup_count={tracker.dup_count} last_ack={tracker.last_ack}")

    fresh_dup = on_ack(tracker, 2000)
    marker = "OK" if fresh_dup is AckSignal.DUPLICATE and tracker.dup_count == 1 else "NG"
    print(f"[{marker}] counting starts over from 1   -> {fresh_dup.value} dup_count={tracker.dup_count}")


if __name__ == "__main__":
    main()
