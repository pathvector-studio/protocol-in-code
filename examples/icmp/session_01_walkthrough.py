from protocol_in_code.icmp.message import IcmpMessage, IcmpType, QuotedPacket, validate_message


def main() -> None:
    print("Session 01 walkthrough: An error is a packet about a packet")
    print()

    quote = QuotedPacket(
        src_ip="198.51.100.5",
        dst_ip="203.0.113.9",
        protocol="UDP",
        src_port=53421,
        dst_port=33434,
    )

    error_with_quote = IcmpMessage(
        icmp_type=IcmpType.TIME_EXCEEDED,
        code="TTL expired in transit",
        quoted=quote,
    )
    marker = "OK" if validate_message(error_with_quote) else "NG"
    print(f"[{marker}] error WITH a quote           -> valid")

    error_without_quote = IcmpMessage(
        icmp_type=IcmpType.DEST_UNREACHABLE,
        code="Host Unreachable",
        quoted=None,
    )
    marker = "OK" if not validate_message(error_without_quote) else "NG"
    print(f"[{marker}] error WITHOUT a quote         -> invalid")

    echo_with_quote = IcmpMessage(
        icmp_type=IcmpType.ECHO_REQUEST,
        code="0",
        quoted=quote,
    )
    marker = "OK" if not validate_message(echo_with_quote) else "NG"
    print(f"[{marker}] echo WITH a quote             -> invalid")

    echo_without_quote = IcmpMessage(
        icmp_type=IcmpType.ECHO_REPLY,
        code="0",
        quoted=None,
    )
    marker = "OK" if validate_message(echo_without_quote) else "NG"
    print(f"[{marker}] echo WITHOUT a quote          -> valid")

    ports_readable = (
        error_with_quote.quoted.src_port == 53421 and error_with_quote.quoted.dst_port == 33434
    )
    marker = "OK" if ports_readable else "NG"
    print(f"[{marker}] quote's ports readable        -> src {quote.src_port} dst {quote.dst_port}")

    same_socket = (
        error_with_quote.quoted.protocol == quote.protocol
        and error_with_quote.quoted.src_port == quote.src_port
    )
    marker = "OK" if same_socket else "NG"
    print(f"[{marker}] error maps back to one socket -> {quote.protocol} {quote.src_port}")


if __name__ == "__main__":
    main()
