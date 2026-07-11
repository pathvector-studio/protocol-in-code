from protocol_in_code.ice.stun import behind_nat, stun_query


def main() -> None:
    print("Session 01 walkthrough: STUN tells you your own address")
    print()

    local_ip, local_port = "10.0.0.5", 55555
    server = "stun.example.net"

    no_nat = stun_query(local_ip, local_port, nat_mapping=None, server=server)
    marker = "OK" if (no_nat.mapped_ip, no_nat.mapped_port) == (local_ip, local_port) else "NG"
    print(f"[{marker}] no NAT: response echoes local    -> {no_nat.mapped_ip}:{no_nat.mapped_port}")

    marker = "OK" if behind_nat((local_ip, local_port), no_nat) is False else "NG"
    print(f"[{marker}] no NAT: behind_nat is False       -> {behind_nat((local_ip, local_port), no_nat)}")

    def cone_nat(from_ip: str, from_port: int, server: str) -> tuple[str, int]:
        # A NAT in the path rewrites the envelope: same client, different
        # address as observed from outside. The mapping does not depend on
        # from_ip/from_port's values beyond identifying the client; it is
        # just standing in for "something out there rewrote this."
        return "203.0.113.9", 62000

    with_nat = stun_query(local_ip, local_port, nat_mapping=cone_nat, server=server)
    marker = "OK" if (with_nat.mapped_ip, with_nat.mapped_port) != (local_ip, local_port) else "NG"
    print(f"[{marker}] with NAT: response differs        -> {with_nat.mapped_ip}:{with_nat.mapped_port}")

    marker = "OK" if behind_nat((local_ip, local_port), with_nat) is True else "NG"
    print(f"[{marker}] with NAT: behind_nat is True       -> {behind_nat((local_ip, local_port), with_nat)}")

    # The headline: you learned this from the outside. Nothing local told the
    # client its own mapped address changed - the comparison against what the
    # server actually saw is the entire discovery.
    marker = "OK" if with_nat.mapped_ip == "203.0.113.9" and with_nat.mapped_port == 62000 else "NG"
    print(f"[{marker}] response carries exactly what the server saw -> {with_nat.mapped_ip}:{with_nat.mapped_port}")

    same_local_again = stun_query(local_ip, local_port, nat_mapping=cone_nat, server=server)
    marker = "OK" if same_local_again == with_nat else "NG"
    print(f"[{marker}] same local, same NAT -> same mapped addr      -> {same_local_again.mapped_ip}:{same_local_again.mapped_port}")


if __name__ == "__main__":
    main()
