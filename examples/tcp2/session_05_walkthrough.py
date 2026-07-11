from protocol_in_code.tcp2.backlog import (
    AckOutcome,
    ListenBacklog,
    SynOutcome,
    app_accept,
    on_final_ack,
    on_syn,
)


def main() -> None:
    print("Session 05 walkthrough: The backlog is two queues")
    print()

    backlog = ListenBacklog(syn_limit=2, accept_limit=1)

    first_syn = on_syn(backlog, ("198.51.100.1", 1111), now=0)
    marker = "OK" if first_syn is SynOutcome.QUEUED else "NG"
    print(f"[{marker}] SYN #1 queues              -> {first_syn.value}")

    second_syn = on_syn(backlog, ("198.51.100.2", 2222), now=0)
    marker = "OK" if second_syn is SynOutcome.QUEUED else "NG"
    print(f"[{marker}] SYN #2 queues (at limit)   -> {second_syn.value}")

    third_syn = on_syn(backlog, ("198.51.100.3", 3333), now=0)
    marker = "OK" if third_syn is SynOutcome.DROPPED_SYN_QUEUE_FULL else "NG"
    print(f"[{marker}] SYN #3 dropped, queue full -> {third_syn.value}")

    first_ack = on_final_ack(backlog, ("198.51.100.1", 1111))
    marker = "OK" if first_ack is AckOutcome.MOVED_TO_ACCEPT_QUEUE else "NG"
    print(f"[{marker}] final ACK #1 moves along   -> {first_ack.value}")

    second_ack = on_final_ack(backlog, ("198.51.100.2", 2222))
    accept_full = second_ack is AckOutcome.ACCEPT_QUEUE_FULL
    entry_survives = ("198.51.100.2", 2222) in backlog.syn_queue
    marker = "OK" if accept_full and entry_survives else "NG"
    print(f"[{marker}] final ACK #2: accept full, syn_queue entry stays -> {second_ack.value}, still queued={entry_survives}")

    unknown = on_final_ack(backlog, ("198.51.100.9", 9999))
    marker = "OK" if unknown is AckOutcome.UNKNOWN_CLIENT else "NG"
    print(f"[{marker}] ACK for a client never SYNed -> {unknown.value}")

    accepted = app_accept(backlog)
    marker = "OK" if accepted == ("198.51.100.1", 1111) else "NG"
    print(f"[{marker}] app_accept() drains FIFO   -> {accepted}")

    empty = app_accept(backlog)
    marker = "OK" if empty is None else "NG"
    print(f"[{marker}] app_accept() on empty queue -> {empty}")


if __name__ == "__main__":
    main()
