from protocol_in_code.arp.pending import (
    MAX_QUEUE_PER_IP,
    EnqueueOutcome,
    PendingQueue,
    drop_all,
    enqueue,
    flush,
)


def main() -> None:
    print("Session 02 walkthrough: Packets wait for answers")
    print()

    queue = PendingQueue()
    ip = "10.0.0.2"

    first = enqueue(queue, ip, "packet-1")
    marker = "OK" if first is EnqueueOutcome.QUEUED and queue.waiting[ip] == ("packet-1",) else "NG"
    print(f"[{marker}] first packet queues           -> {first.value} {queue.waiting[ip]}")

    second = enqueue(queue, ip, "packet-2")
    marker = "OK" if second is EnqueueOutcome.QUEUED and queue.waiting[ip] == ("packet-1", "packet-2") else "NG"
    print(f"[{marker}] second packet queues in order -> {second.value} {queue.waiting[ip]}")

    third = enqueue(queue, ip, "packet-3")
    marker = "OK" if third is EnqueueOutcome.QUEUED and queue.waiting[ip] == ("packet-1", "packet-2", "packet-3") else "NG"
    print(f"[{marker}] third packet fills the line   -> {third.value} {queue.waiting[ip]}")

    fourth = enqueue(queue, ip, "packet-4")
    marker = "OK" if fourth is EnqueueOutcome.QUEUED_DROPPED_OLDEST and queue.waiting[ip] == ("packet-2", "packet-3", "packet-4") else "NG"
    print(f"[{marker}] fourth packet drops the oldest -> {fourth.value} {queue.waiting[ip]}")

    marker = "OK" if len(queue.waiting[ip]) == MAX_QUEUE_PER_IP else "NG"
    print(f"[{marker}] queue never exceeds the cap   -> len={len(queue.waiting[ip])} cap={MAX_QUEUE_PER_IP}")

    delivered = flush(queue, ip)
    marker = "OK" if delivered == ("packet-2", "packet-3", "packet-4") else "NG"
    print(f"[{marker}] flush returns the survivors   -> {delivered}")

    marker = "OK" if ip not in queue.waiting else "NG"
    print(f"[{marker}] flush empties the line        -> {ip in queue.waiting}")

    other_ip = "10.0.0.9"
    enqueue(queue, other_ip, "packet-a")
    enqueue(queue, other_ip, "packet-b")
    drop_all(queue, other_ip)
    marker = "OK" if other_ip not in queue.waiting else "NG"
    print(f"[{marker}] drop_all empties without a return -> {other_ip in queue.waiting}")


if __name__ == "__main__":
    main()
