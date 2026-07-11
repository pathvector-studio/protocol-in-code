from protocol_in_code.rip.route import RipRoute, RouteValidity, better, validate_route


def main() -> None:
    print("Session 01 walkthrough: A route is a rumor with a distance")
    print()

    route = RipRoute(prefix="10.0.0.0/24", metric=3, next_hop="192.0.2.1", learned_from="192.0.2.1")
    print(f"[OK] a route prints         -> {route}")

    negative = RipRoute(prefix="10.0.0.0/24", metric=-1, next_hop="192.0.2.1", learned_from="192.0.2.1")
    verdict = validate_route(negative)
    marker = "OK" if verdict is RouteValidity.NEGATIVE_METRIC else "NG"
    print(f"[{marker}] metric -1              -> {verdict.value}")

    too_high = RipRoute(prefix="10.0.0.0/24", metric=17, next_hop="192.0.2.1", learned_from="192.0.2.1")
    verdict = validate_route(too_high)
    marker = "OK" if verdict is RouteValidity.METRIC_TOO_HIGH else "NG"
    print(f"[{marker}] metric 17              -> {verdict.value}")

    unreachable = RipRoute(prefix="10.0.0.0/24", metric=16, next_hop="192.0.2.1", learned_from="192.0.2.1")
    verdict = validate_route(unreachable)
    marker = "OK" if verdict is RouteValidity.VALID else "NG"
    print(f"[{marker}] metric 16 (infinity)   -> {verdict.value}")

    closer = RipRoute(prefix="10.0.0.0/24", metric=2, next_hop="192.0.2.9", learned_from="192.0.2.9")
    marker = "OK" if better(closer, route) else "NG"
    print(f"[{marker}] metric 2 vs metric 3   -> better(closer, route) = {better(closer, route)}")

    farther = RipRoute(prefix="10.0.0.0/24", metric=5, next_hop="192.0.2.9", learned_from="192.0.2.9")
    marker = "OK" if not better(farther, route) else "NG"
    print(f"[{marker}] metric 5 vs metric 3   -> better(farther, route) = {better(farther, route)}")

    tied = RipRoute(prefix="10.0.0.0/24", metric=3, next_hop="192.0.2.9", learned_from="192.0.2.9")
    marker = "OK" if not better(tied, route) and not better(route, tied) else "NG"
    print(f"[{marker}] metric 3 vs metric 3   -> neither is better on a tie (strict < only)")


if __name__ == "__main__":
    main()
