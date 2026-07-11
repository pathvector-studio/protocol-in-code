from protocol_in_code.rip.infinity import INFINITY, clamp_metric, is_unreachable, poison
from protocol_in_code.rip.route import RipRoute


def main() -> None:
    print("Session 03 walkthrough: Sixteen means unreachable")
    print()

    just_over = clamp_metric(15 + 1)
    marker = "OK" if just_over == INFINITY else "NG"
    print(f"[{marker}] clamp(15 + 1)              -> {just_over}")

    far_over = clamp_metric(100)
    marker = "OK" if far_over == INFINITY else "NG"
    print(f"[{marker}] clamp(100)                 -> {far_over}")

    at_boundary = is_unreachable(16)
    marker = "OK" if at_boundary else "NG"
    print(f"[{marker}] is_unreachable(16)         -> {at_boundary}")

    below_boundary = is_unreachable(15)
    marker = "OK" if not below_boundary else "NG"
    print(f"[{marker}] is_unreachable(15)         -> {below_boundary}")

    route = RipRoute(prefix="10.0.0.0/24", metric=3, next_hop="192.0.2.1", learned_from="192.0.2.1")
    poisoned = poison(route)
    marker = "OK" if poisoned.metric == INFINITY else "NG"
    print(f"[{marker}] poison() sets metric       -> {poisoned.metric}")

    fields_preserved = (
        poisoned.prefix == route.prefix
        and poisoned.next_hop == route.next_hop
        and poisoned.learned_from == route.learned_from
    )
    marker = "OK" if fields_preserved else "NG"
    print(f"[{marker}] poison() keeps other fields -> prefix={poisoned.prefix}, next_hop={poisoned.next_hop}, learned_from={poisoned.learned_from}")


if __name__ == "__main__":
    main()
