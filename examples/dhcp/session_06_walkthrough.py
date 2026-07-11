from protocol_in_code.dhcp.discover import DhcpMessage, MessageType
from protocol_in_code.dhcp.pool import AddressPool
from protocol_in_code.dhcp.server_loop import ToyDhcpServer, run_dora


def main() -> None:
    print("Session 06 walkthrough: Build the toy DHCP server loop")
    print()

    server = ToyDhcpServer(pool=AddressPool(network_prefix="192.0.2"), server_id="server-1")

    messages = run_dora(server, client_mac="AA:BB:CC:00:11:22", transaction_id=1)
    marker = "OK" if len(messages) == 4 else "NG"
    print(f"[{marker}] run_dora returns exactly four messages -> count={len(messages)}")

    expected_types = (MessageType.DISCOVER, MessageType.OFFER, MessageType.REQUEST, MessageType.ACK)
    actual_types = tuple(msg.message_type for msg in messages)
    marker = "OK" if actual_types == expected_types else "NG"
    labels = "/".join(t.value[0] for t in actual_types)
    print(f"[{marker}] D-O-R-A in order                       -> {labels} ({', '.join(t.value for t in actual_types)})")

    discover, offer_msg, request, ack = messages
    granted_ip = ack.offered_ip

    lookup = server.lease_table.leases.get("AA:BB:CC:00:11:22")
    marker = "OK" if lookup is not None and lookup.ip == granted_ip else "NG"
    print(f"[{marker}] lease exists in lease_table after ACK  -> ip={lookup.ip if lookup else None}")

    second_messages = run_dora(server, client_mac="AA:BB:CC:00:33:44", transaction_id=2)
    second_ip = second_messages[3].offered_ip
    marker = "OK" if second_ip is not None and second_ip != granted_ip else "NG"
    print(f"[{marker}] second client gets a different ip      -> {second_ip} (first was {granted_ip})")

    wrong_server_request = DhcpMessage(
        message_type=MessageType.REQUEST,
        transaction_id=3,
        client_mac="AA:BB:CC:00:55:66",
        server_id="server-2",
        requested_ip="192.0.2.10",
    )
    nak = server.on_message(wrong_server_request)
    marker = "OK" if nak is not None and nak.message_type is MessageType.NAK else "NG"
    print(f"[{marker}] REQUEST naming another server -> NAK    -> {nak.message_type.value if nak else None}")

    hold_released = "AA:BB:CC:00:55:66" not in server._outstanding_offers
    marker = "OK" if hold_released else "NG"
    print(f"[{marker}] losing server's hold released           -> outstanding offer cleared={hold_released}")

    marker = "OK" if len(server.trace) > 0 else "NG"
    print(f"[{marker}] trace is non-empty                      -> {len(server.trace)} lines")

    granted_line_present = any("granted" in line and "ACK" in line for line in server.trace)
    marker = "OK" if granted_line_present else "NG"
    print(f"[{marker}] trace records the granted line          -> {[l for l in server.trace if 'granted' in l][:1]}")


if __name__ == "__main__":
    main()
