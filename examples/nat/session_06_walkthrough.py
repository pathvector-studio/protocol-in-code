from protocol_in_code.nat.five_tuple import FiveTuple, reply_tuple
from protocol_in_code.nat.nat_loop import ToyNatBox, run_flow
from protocol_in_code.nat.rewrite import Packet


def main() -> None:
    print("Session 06 walkthrough: Build the toy NAT box loop")
    print()

    box = ToyNatBox(public_ip="203.0.113.9")

    private_tuple = FiveTuple(protocol="udp", src_ip="10.0.0.5", src_port=51000, dst_ip="8.8.8.8", dst_port=53)

    translated, delivered = run_flow(box, private_tuple)

    translated_ok = (
        translated is not None
        and translated.tuple.src_ip == box.public_ip
        and translated.tuple.src_port in box.allocator.in_use
    )
    marker = "OK" if translated_ok else "NG"
    print(f"[{marker}] outbound translated to public ip + ephemeral port -> {translated.tuple.src_ip}:{translated.tuple.src_port}")

    delivered_ok = delivered is not None and delivered.tuple == reply_tuple(private_tuple)
    marker = "OK" if delivered_ok else "NG"
    print(f"[{marker}] delivered == reply_tuple(private), NOT private_tuple itself -> {delivered.tuple}")

    addressed_to_private_host = (
        delivered.tuple.dst_ip == private_tuple.src_ip
        and delivered.tuple.dst_port == private_tuple.src_port
    )
    marker = "OK" if addressed_to_private_host else "NG"
    print(f"[{marker}] delivered packet is addressed to the private host's own src -> dst={delivered.tuple.dst_ip}:{delivered.tuple.dst_port}")

    first_public_port = translated.tuple.src_port
    second_out = box.outbound(Packet(tuple=private_tuple, payload_note="request-2"))
    reused_port = second_out is not None and second_out.tuple.src_port == first_public_port
    marker = "OK" if reused_port else "NG"
    print(f"[{marker}] second outbound on same flow reuses the port, no new allocation -> {second_out.tuple.src_port}")

    unsolicited = Packet(
        tuple=FiveTuple(protocol="udp", src_ip="1.2.3.4", src_port=9999, dst_ip=box.public_ip, dst_port=54321),
        payload_note="unsolicited",
    )
    dropped = box.inbound(unsolicited)
    marker = "OK" if dropped is None else "NG"
    print(f"[{marker}] inbound with no matching entry is dropped (accidental firewall) -> {dropped}")

    box.tick(31)
    entry_swept = private_tuple not in box.table.entries
    marker = "OK" if entry_swept else "NG"
    print(f"[{marker}] tick() past the 30s udp timeout sweeps the idle flow's table entry -> {private_tuple in box.table.entries}")

    port_reclaimed = first_public_port not in box.allocator.in_use
    marker = "OK" if port_reclaimed else "NG"
    print(f"[{marker}] the expired flow's public port returns to the pool -> {first_public_port} in_use={first_public_port in box.allocator.in_use}")

    late_reply_tuple = FiveTuple(
        protocol="udp", src_ip="8.8.8.8", src_port=53, dst_ip=box.public_ip, dst_port=first_public_port,
    )
    late_delivered = box.inbound(Packet(tuple=late_reply_tuple, payload_note="late-response"))
    marker = "OK" if late_delivered is None else "NG"
    print(f"[{marker}] reply arriving after expiry finds NO_MATCH, dropped silently -> {late_delivered}")


if __name__ == "__main__":
    main()
