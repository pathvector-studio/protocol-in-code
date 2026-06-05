from protocol_in_code.ospf.cost import select_best_route, select_best_routes
from protocol_in_code.ospf.routing import OSPFRoute


def main() -> None:
    candidates = (
        OSPFRoute(prefix="10.0.9.0/24", next_hop_router_id="2.2.2.2", total_cost=20, area_id="0.0.0.0"),
        OSPFRoute(prefix="10.0.9.0/24", next_hop_router_id="3.3.3.3", total_cost=15, area_id="0.0.0.0"),
        OSPFRoute(prefix="10.0.9.0/24", next_hop_router_id="4.4.4.4", total_cost=15, area_id="0.0.0.1"),
    )
    decision = select_best_route(candidates)
    best_routes = select_best_routes(
        candidates
        + (
            OSPFRoute(prefix="10.0.10.0/24", next_hop_router_id="5.5.5.5", total_cost=30, area_id="0.0.0.0"),
        )
    )

    print("winner:", decision.winner.next_hop_router_id if decision else None)
    print("winner_cost:", decision.winner.total_cost if decision else None)
    print("best_prefixes:", [route.prefix for route in best_routes])


if __name__ == "__main__":
    main()

