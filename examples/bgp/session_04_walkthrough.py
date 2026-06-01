from protocol_in_code.bgp.validation import BGPRoute, VRP, validate_origin


def main() -> None:
    vrps = [
        VRP(prefix="203.0.113.0/24", max_length=24, origin_as=65001),
        VRP(prefix="198.51.100.0/24", max_length=25, origin_as=65010),
    ]

    scenarios = (
        ("valid exact match", BGPRoute(prefix="203.0.113.0/24", origin_as=65001)),
        ("invalid origin mismatch", BGPRoute(prefix="203.0.113.0/24", origin_as=65003)),
        ("not found no covering vrp", BGPRoute(prefix="192.0.2.0/24", origin_as=65020)),
        ("valid more specific within max length", BGPRoute(prefix="198.51.100.0/25", origin_as=65010)),
        ("not found more specific exceeds max length", BGPRoute(prefix="198.51.100.0/26", origin_as=65010)),
    )

    print("Session 04 walkthrough: Origin validation is a separate decision")
    print()
    for title, route in scenarios:
        state = validate_origin(route, vrps)
        print(f"- {title}")
        print(f"  route: prefix={route.prefix}, origin_as={route.origin_as}")
        print(f"  result: {state.value}")
        print()


if __name__ == "__main__":
    main()
