from protocol_in_code.tcp.segment import Segment
from protocol_in_code.tcp.teardown import (
    TWO_MSL,
    CloseState,
    initiate_close,
    on_segment_active,
    on_segment_passive,
    passive_close,
    time_wait_expired,
)


def main() -> None:
    print("Session 09 walkthrough: Goodbye takes four packets (and a wait)")
    print()

    segments_on_wire = []

    # --- Active side: client initiates the close from ESTABLISHED ---
    client_state, client_fin = initiate_close(seq=1000)
    segments_on_wire.append(client_fin)
    marker = "OK" if client_state is CloseState.FIN_WAIT_1 else "NG"
    print(f"[{marker}] client initiate_close        -> state={client_state.value} seq={client_fin.seq}")

    # Peer acks our FIN first (no FIN from them yet): FIN_WAIT_1 -> FIN_WAIT_2
    peer_ack = Segment(seq=5000, ack=client_fin.seq + 1, flags=frozenset({"ACK"}))
    step = on_segment_active(client_state, peer_ack, now=0)
    client_state = step.new_state
    marker = "OK" if client_state is CloseState.FIN_WAIT_2 and step.reply is None else "NG"
    print(f"[{marker}] client hears ACK of our FIN  -> state={client_state.value}")

    # Peer's own FIN arrives: FIN_WAIT_2 -> TIME_WAIT, and we ack it (segment #2 out)
    peer_fin = Segment(seq=5000, ack=client_fin.seq + 1, flags=frozenset({"FIN"}))
    step = on_segment_active(client_state, peer_fin, now=10)
    client_state = step.new_state
    segments_on_wire.append(step.reply)
    marker = "OK" if (
        client_state is CloseState.TIME_WAIT and step.reply is not None and step.wait_started_at == 10
    ) else "NG"
    print(f"[{marker}] client hears peer's FIN      -> state={client_state.value} wait_started_at={step.wait_started_at}")

    # --- Passive side: server hears the client's original FIN from ESTABLISHED ---
    server_state = CloseState.ESTABLISHED
    step = on_segment_passive(server_state, client_fin)
    server_state = step.new_state
    segments_on_wire.append(step.reply)
    marker = "OK" if server_state is CloseState.CLOSE_WAIT and step.reply is not None else "NG"
    print(f"[{marker}] server hears client's FIN    -> state={server_state.value}")

    # Server's local application finally calls close(): CLOSE_WAIT -> LAST_ACK, sends its own FIN
    server_state, server_fin = passive_close(seq=5000)
    segments_on_wire.append(server_fin)
    marker = "OK" if server_state is CloseState.LAST_ACK else "NG"
    print(f"[{marker}] server app calls close()     -> state={server_state.value} seq={server_fin.seq}")

    # Client's TIME_WAIT ack of the peer FIN above (segment #2) is what the server treats as
    # the last ack once it reflects back client's ack of server_fin: LAST_ACK -> CLOSED
    last_ack = Segment(seq=client_fin.seq + 1, ack=server_fin.seq + 1, flags=frozenset({"ACK"}))
    step = on_segment_passive(server_state, last_ack)
    server_state = step.new_state
    marker = "OK" if server_state is CloseState.CLOSED and step.reply is None else "NG"
    print(f"[{marker}] server hears last ACK        -> state={server_state.value}")

    marker = "OK" if len(segments_on_wire) == 4 else "NG"
    print(f"[{marker}] exactly four segments sent   -> count={len(segments_on_wire)}")

    # --- TIME_WAIT expiry is arithmetic, not a segment ---
    entered_at = 10
    one_tick_early = time_wait_expired(entered_at, now=entered_at + TWO_MSL - 1)
    marker = "OK" if one_tick_early is False else "NG"
    print(f"[{marker}] one tick before TWO_MSL      -> expired={one_tick_early}")

    at_boundary = time_wait_expired(entered_at, now=entered_at + TWO_MSL)
    marker = "OK" if at_boundary is True else "NG"
    print(f"[{marker}] exactly at TWO_MSL           -> expired={at_boundary}")


if __name__ == "__main__":
    main()
