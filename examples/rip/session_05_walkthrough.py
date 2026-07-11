from protocol_in_code.rip.infinity import INFINITY
from protocol_in_code.rip.route import RipRoute
from protocol_in_code.rip.split_horizon import advertisable, advertisable_with_poison
from protocol_in_code.rip.update import RoutingTable


def main() -> None:
    print("Session 05 walkthrough: Don't tell me what I told you")
    print()

    table = RoutingTable(
        routes={
            "10.0.0.0/24": RipRoute("10.0.0.0/24", metric=2, next_hop="B", learned_from="B"),
            "10.0.1.0/24": RipRoute("10.0.1.0/24", metric=3, next_hop="C", learned_from="C"),
        }
    )

    to_b = advertisable(table, to_neighbor="B")
    marker = "OK" if ("10.0.0.0/24", 2) not in to_b else "NG"
    print(f"[{marker}] B-learned route omitted when advertising to B -> {to_b}")

    to_c = advertisable(table, to_neighbor="C")
    marker = "OK" if ("10.0.0.0/24", 2) in to_c else "NG"
    print(f"[{marker}] same route present when advertising to C      -> {to_c}")

    poisoned_to_b = advertisable_with_poison(table, to_neighbor="B")
    marker = "OK" if ("10.0.0.0/24", INFINITY) in poisoned_to_b else "NG"
    print(f"[{marker}] with poison, it appears to B at INFINITY       -> {poisoned_to_b}")

    plain_to_b = set(advertisable(table, to_neighbor="B"))
    poison_to_b = set(advertisable_with_poison(table, to_neighbor="B"))
    diff = poison_to_b - plain_to_b
    marker = "OK" if diff == {("10.0.0.0/24", INFINITY)} else "NG"
    print(f"[{marker}] the two functions differ on exactly one route  -> {diff}")

    plain_to_c = set(advertisable(table, to_neighbor="C"))
    poison_to_c = set(advertisable_with_poison(table, to_neighbor="C"))
    diff_c = poison_to_c - plain_to_c
    marker = "OK" if diff_c == {("10.0.1.0/24", INFINITY)} else "NG"
    print(f"[{marker}] and agree everywhere except the neighbor's own route -> {diff_c}")

    marker = "OK" if len(to_b) == len(table.routes) - 1 else "NG"
    print(f"[{marker}] plain split horizon shrinks the advertisement  -> len={len(to_b)}")

    marker = "OK" if len(poisoned_to_b) == len(table.routes) else "NG"
    print(f"[{marker}] poisoned reverse keeps the same route count    -> len={len(poisoned_to_b)}")


if __name__ == "__main__":
    main()
