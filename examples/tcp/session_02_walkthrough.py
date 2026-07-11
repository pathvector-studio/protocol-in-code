from protocol_in_code.tcp.handshake import ConnectionState, active_open, on_segment
from protocol_in_code.tcp.segment import is_ack, is_syn


def main() -> None:
    print("Session 02 walkthrough: It takes three packets to say hello")
    print()

    segments_on_wire = []

    client_iss = 1000
    server_iss = 5000

    client_state, syn = active_open(client_iss)
    segments_on_wire.append(syn)
    marker = "OK" if client_state is ConnectionState.SYN_SENT and is_syn(syn) else "NG"
    print(f"[{marker}] client active_open          -> state={client_state.value} seq={syn.seq}")

    server_state = ConnectionState.LISTEN
    server_step = on_segment(server_state, syn, server_iss)
    segments_on_wire.append(server_step.reply)
    server_state = server_step.new_state
    syn_ack = server_step.reply
    marker = "OK" if (
        server_state is ConnectionState.SYN_RCVD
        and syn_ack is not None
        and is_syn(syn_ack)
        and is_ack(syn_ack)
        and syn_ack.ack == syn.seq + 1
    ) else "NG"
    print(f"[{marker}] server hears SYN            -> state={server_state.value} seq={syn_ack.seq} ack={syn_ack.ack}")

    client_step = on_segment(client_state, syn_ack, client_iss)
    segments_on_wire.append(client_step.reply)
    client_state = client_step.new_state
    final_ack = client_step.reply
    marker = "OK" if (
        client_state is ConnectionState.ESTABLISHED
        and final_ack is not None
        and is_ack(final_ack)
        and not is_syn(final_ack)
        and final_ack.seq == syn_ack.ack
        and final_ack.ack == syn_ack.seq + 1
    ) else "NG"
    print(f"[{marker}] client hears SYN+ACK        -> state={client_state.value} seq={final_ack.seq} ack={final_ack.ack}")

    server_step_final = on_segment(server_state, final_ack, server_iss)
    server_state = server_step_final.new_state
    marker = "OK" if server_state is ConnectionState.ESTABLISHED and server_step_final.reply is None else "NG"
    print(f"[{marker}] server hears final ACK      -> state={server_state.value} reply={server_step_final.reply}")

    both_established = client_state is ConnectionState.ESTABLISHED and server_state is ConnectionState.ESTABLISHED
    marker = "OK" if both_established else "NG"
    print(f"[{marker}] both sides established      -> client={client_state.value} server={server_state.value}")

    segment_count = len(segments_on_wire)
    marker = "OK" if segment_count == 3 else "NG"
    print(f"[{marker}] exactly three segments sent -> count={segment_count}")

    late_syn = on_segment(client_state, syn, client_iss)
    marker = "OK" if late_syn.new_state is ConnectionState.ESTABLISHED and late_syn.reply is None else "NG"
    print(f"[{marker}] handshake ignored once done -> {late_syn.note}")


if __name__ == "__main__":
    main()
