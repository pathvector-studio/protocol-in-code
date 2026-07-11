from protocol_in_code.nat.five_tuple import FiveTuple, TupleValidity, reply_tuple, validate_tuple


def main() -> None:
    print("Session 01 walkthrough: A connection is a 5-tuple")
    print()

    outbound = FiveTuple(protocol="tcp", src_ip="10.0.0.5", src_port=51000, dst_ip="93.184.216.34", dst_port=443)

    valid = validate_tuple(outbound)
    marker = "OK" if valid is TupleValidity.VALID else "NG"
    print(f"[{marker}] well-formed tuple            -> {valid.value}")

    bad_src_port = FiveTuple(protocol="tcp", src_ip="10.0.0.5", src_port=0, dst_ip="93.184.216.34", dst_port=443)
    checked = validate_tuple(bad_src_port)
    marker = "OK" if checked is TupleValidity.BAD_SRC_PORT else "NG"
    print(f"[{marker}] src_port 0 is out of range   -> {checked.value}")

    bad_dst_port = FiveTuple(protocol="tcp", src_ip="10.0.0.5", src_port=51000, dst_ip="93.184.216.34", dst_port=70000)
    checked = validate_tuple(bad_dst_port)
    marker = "OK" if checked is TupleValidity.BAD_DST_PORT else "NG"
    print(f"[{marker}] dst_port 70000 is out of range -> {checked.value}")

    unknown_protocol = FiveTuple(protocol="icmp", src_ip="10.0.0.5", src_port=51000, dst_ip="93.184.216.34", dst_port=443)
    checked = validate_tuple(unknown_protocol)
    marker = "OK" if checked is TupleValidity.UNKNOWN_PROTOCOL else "NG"
    print(f"[{marker}] icmp is not tcp or udp       -> {checked.value}")

    reply = reply_tuple(outbound)
    swapped = (
        reply.src_ip == outbound.dst_ip
        and reply.src_port == outbound.dst_port
        and reply.dst_ip == outbound.src_ip
        and reply.dst_port == outbound.src_port
    )
    marker = "OK" if swapped else "NG"
    print(f"[{marker}] reply_tuple swaps src/dst    -> {reply.src_ip}:{reply.src_port} -> {reply.dst_ip}:{reply.dst_port}")

    round_trip = reply_tuple(reply_tuple(outbound))
    marker = "OK" if round_trip == outbound else "NG"
    print(f"[{marker}] reply_tuple is an involution -> reply_tuple(reply_tuple(t)) == t")


if __name__ == "__main__":
    main()
