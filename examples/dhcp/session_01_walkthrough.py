import dataclasses

from protocol_in_code.dhcp.discover import (
    DhcpMessage,
    MessageType,
    MessageValidity,
    make_discover,
    validate_message,
)


def main() -> None:
    print("Session 01 walkthrough: Discovery is shouting into the dark")
    print()

    discover = make_discover(client_mac="aa:bb:cc:00:00:01", transaction_id=1)

    field_names = {f.name for f in dataclasses.fields(discover)}
    marker = "OK" if "dest" not in field_names else "NG"
    print(f"[{marker}] DISCOVER has no dest field at all -> fields={sorted(field_names)}")

    marker = "OK" if discover.message_type is MessageType.DISCOVER else "NG"
    print(f"[{marker}] make_discover produces a DISCOVER    -> {discover.message_type.value}")

    offer = DhcpMessage(
        message_type=MessageType.OFFER,
        transaction_id=1,
        client_mac="aa:bb:cc:00:00:01",
        offered_ip="192.0.2.10",
        server_id="192.0.2.1",
    )
    result = validate_message(offer)
    marker = "OK" if result is MessageValidity.VALID else "NG"
    print(f"[{marker}] OFFER with offered_ip is valid        -> {result.value}")

    offer_missing_ip = DhcpMessage(
        message_type=MessageType.OFFER,
        transaction_id=1,
        client_mac="aa:bb:cc:00:00:01",
        server_id="192.0.2.1",
    )
    result = validate_message(offer_missing_ip)
    marker = "OK" if result is MessageValidity.MISSING_OFFERED_IP else "NG"
    print(f"[{marker}] OFFER without offered_ip is invalid   -> {result.value}")

    request_missing_server = DhcpMessage(
        message_type=MessageType.REQUEST,
        transaction_id=1,
        client_mac="aa:bb:cc:00:00:01",
        requested_ip="192.0.2.10",
    )
    result = validate_message(request_missing_server)
    marker = "OK" if result is MessageValidity.MISSING_SERVER_ID else "NG"
    print(f"[{marker}] REQUEST without server_id is invalid  -> {result.value}")

    request_valid = DhcpMessage(
        message_type=MessageType.REQUEST,
        transaction_id=1,
        client_mac="aa:bb:cc:00:00:01",
        server_id="192.0.2.1",
        requested_ip="192.0.2.10",
    )
    result = validate_message(request_valid)
    marker = "OK" if result is MessageValidity.VALID else "NG"
    print(f"[{marker}] REQUEST with server_id is valid       -> {result.value}")


if __name__ == "__main__":
    main()
