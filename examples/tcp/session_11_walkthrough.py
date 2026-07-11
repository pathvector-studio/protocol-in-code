from protocol_in_code.tcp.segment import Segment
from protocol_in_code.tcp.speaker import ToyTcpEndpoint, run_three_way_handshake
from protocol_in_code.tcp.teardown import TWO_MSL, CloseState


def main() -> None:
    print("Session 11 walkthrough: Build the toy TCP loop")
    print()

    client = ToyTcpEndpoint(name="client", iss=1000)
    server = ToyTcpEndpoint(name="server", iss=5000)

    # --- Handshake: three segments, both endpoints reach ESTABLISHED ---
    run_three_way_handshake(client, server)
    marker = "OK" if (
        client.state is client.state.__class__.ESTABLISHED
        and server.state is server.state.__class__.ESTABLISHED
        and client.state.value == "Established"
        and server.state.value == "Established"
    ) else "NG"
    print(f"[{marker}] handshake reaches ESTABLISHED -> client={client.state.value} server={server.state.value}")

    # --- One data segment delivered: server's rcv_nxt advances past it ---
    # rcv_nxt was already set to the final handshake ACK's seq + 1; the next byte of real
    # data must land exactly there for deliver() to accept it instead of treating it as a dup.
    before_rcv_nxt = server.rcv_nxt
    data = Segment(seq=before_rcv_nxt, ack=server.iss + 1, flags=frozenset(), payload_len=1)
    reply = server.on_segment(data)
    marker = "OK" if (
        reply is None and server.rcv_nxt == before_rcv_nxt + 1
    ) else "NG"
    print(f"[{marker}] server delivers one data byte -> rcv_nxt {before_rcv_nxt} -> {server.rcv_nxt}")

    # --- Active close: client initiates, drives through FIN_WAIT_1 -> FIN_WAIT_2 -> TIME_WAIT ---
    client_fin = client.close()
    marker = "OK" if client.state is CloseState.FIN_WAIT_1 else "NG"
    print(f"[{marker}] client close() sends FIN      -> state={client.state.value}")

    # Server, still ESTABLISHED, hears the FIN and moves to CLOSE_WAIT, replying with an ACK
    server_ack_of_fin = server.on_segment(client_fin)
    marker = "OK" if server.state is CloseState.CLOSE_WAIT and server_ack_of_fin is not None else "NG"
    print(f"[{marker}] server hears FIN -> CLOSE_WAIT -> state={server.state.value}")

    # Client hears that ACK: FIN_WAIT_1 -> FIN_WAIT_2
    client.on_segment(server_ack_of_fin)
    marker = "OK" if client.state is CloseState.FIN_WAIT_2 else "NG"
    print(f"[{marker}] client hears ACK of our FIN   -> state={client.state.value}")

    # Server's application closes: CLOSE_WAIT -> LAST_ACK, sends its own FIN
    server_fin = server.close()
    marker = "OK" if server.state is CloseState.LAST_ACK else "NG"
    print(f"[{marker}] server close() sends FIN      -> state={server.state.value}")

    # Client hears server's FIN: FIN_WAIT_2 -> TIME_WAIT, replies with the last ACK
    last_ack = client.on_segment(server_fin)
    marker = "OK" if client.state is CloseState.TIME_WAIT and last_ack is not None else "NG"
    print(f"[{marker}] client hears server's FIN     -> state={client.state.value}")

    # Server hears the last ACK: LAST_ACK -> CLOSED
    server.on_segment(last_ack)
    marker = "OK" if server.state is CloseState.CLOSED else "NG"
    print(f"[{marker}] server hears last ACK         -> state={server.state.value}")

    # Client's TIME_WAIT only resolves once the clock advances past TWO_MSL
    client.tick(TWO_MSL - 1)
    marker = "OK" if client.state is CloseState.TIME_WAIT else "NG"
    print(f"[{marker}] one tick before TWO_MSL       -> state={client.state.value} clock={client.clock}")

    client.tick(1)
    marker = "OK" if client.state is CloseState.CLOSED else "NG"
    print(f"[{marker}] tick reaches TWO_MSL          -> state={client.state.value} clock={client.clock}")

    # --- Both endpoints closed, and their traces tell the whole story ---
    both_closed = client.state is CloseState.CLOSED and server.state is CloseState.CLOSED
    marker = "OK" if both_closed else "NG"
    print(f"[{marker}] both endpoints CLOSED         -> client={client.state.value} server={server.state.value}")

    client_trace_ok = len(client.trace) > 0 and any("active-open" in line for line in client.trace)
    server_trace_ok = len(server.trace) > 0 and any("listening" in line for line in server.trace)
    marker = "OK" if client_trace_ok and server_trace_ok else "NG"
    print(f"[{marker}] both traces non-empty         -> client={len(client.trace)} lines, server={len(server.trace)} lines")


if __name__ == "__main__":
    main()
