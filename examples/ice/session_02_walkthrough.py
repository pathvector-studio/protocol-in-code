from protocol_in_code.ice.nat_behavior import MappingBehavior, Observation, classify_mapping


def main() -> None:
    print("Session 02 walkthrough: NATs have personalities")
    print()

    # Same mapping no matter the destination IP or port -> the most
    # NAT-friendly personality. Two different peers, one stable mapping.
    endpoint_independent = (
        Observation(dest_ip="198.51.100.1", dest_port=3478, mapped_ip="203.0.113.9", mapped_port=62000),
        Observation(dest_ip="198.51.100.2", dest_port=9000, mapped_ip="203.0.113.9", mapped_port=62000),
    )
    verdict = classify_mapping(endpoint_independent)
    marker = "OK" if verdict is MappingBehavior.ENDPOINT_INDEPENDENT else "NG"
    print(f"[{marker}] same mapped addr, dest IP+port both vary -> {verdict.value}")

    # Mapping changes when the destination IP changes, even though within a
    # single dest_ip the mapping stays fixed across ports.
    address_dependent = (
        Observation(dest_ip="198.51.100.1", dest_port=3478, mapped_ip="203.0.113.9", mapped_port=62000),
        Observation(dest_ip="198.51.100.1", dest_port=9000, mapped_ip="203.0.113.9", mapped_port=62000),
        Observation(dest_ip="198.51.100.2", dest_port=3478, mapped_ip="203.0.113.9", mapped_port=62010),
    )
    verdict = classify_mapping(address_dependent)
    marker = "OK" if verdict is MappingBehavior.ADDRESS_DEPENDENT else "NG"
    print(f"[{marker}] same dest IP -> same mapping, diff dest IP -> diff mapping -> {verdict.value}")

    # Mapping changes even for the same destination IP, just because the
    # destination PORT differs -> the strictest, hardest personality.
    address_and_port_dependent = (
        Observation(dest_ip="198.51.100.1", dest_port=3478, mapped_ip="203.0.113.9", mapped_port=62000),
        Observation(dest_ip="198.51.100.1", dest_port=9000, mapped_ip="203.0.113.9", mapped_port=62050),
    )
    verdict = classify_mapping(address_and_port_dependent)
    marker = "OK" if verdict is MappingBehavior.ADDRESS_AND_PORT_DEPENDENT else "NG"
    print(f"[{marker}] same dest IP, diff dest port -> diff mapping -> {verdict.value}")

    # A single observation carries no evidence of change - per the code, one
    # dest_ip mapping to one set of size 1 means neither narrow check fires,
    # so it reads as the most permissive verdict by default.
    single = (
        Observation(dest_ip="198.51.100.1", dest_port=3478, mapped_ip="203.0.113.9", mapped_port=62000),
    )
    verdict = classify_mapping(single)
    marker = "OK" if verdict is MappingBehavior.ENDPOINT_INDEPENDENT else "NG"
    print(f"[{marker}] one observation alone cannot prove anything changes -> {verdict.value}")

    # This is the toy NAT you built in the NAT track: table.py + ports.py key
    # on the full 5-tuple, so a new destination port allocates a fresh
    # mapping even toward the same peer IP. That NAT IS address-and-port
    # dependent, and it is why a reflexive candidate from one STUN server
    # predicts nothing about what a real peer will see.
    toy_nat_box = (
        Observation(dest_ip="192.0.2.50", dest_port=3478, mapped_ip="203.0.113.9", mapped_port=61000),
        Observation(dest_ip="192.0.2.50", dest_port=443, mapped_ip="203.0.113.9", mapped_port=61001),
    )
    verdict = classify_mapping(toy_nat_box)
    marker = "OK" if verdict is MappingBehavior.ADDRESS_AND_PORT_DEPENDENT else "NG"
    print(f"[{marker}] the NAT you built in the NAT track is this one -> {verdict.value}")


if __name__ == "__main__":
    main()
