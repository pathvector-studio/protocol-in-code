from protocol_in_code.stp.path_cost import PORT_COST, PathToRoot, accumulate, better_path
from protocol_in_code.stp.root_election import BridgeId


def main() -> None:
    print("Session 02 walkthrough: Cost decides the path to root")
    print()

    # --- The PORT_COST table: faster is cheaper ---
    slow_cost = PORT_COST[10]
    marker = "OK" if slow_cost == 100 else "NG"
    print(f"[{marker}] 10 Mbps costs 100                  -> PORT_COST[10]={slow_cost}")

    fast_cost = PORT_COST[1000]
    marker = "OK" if fast_cost == 4 else "NG"
    print(f"[{marker}] 1 Gbps costs 4 (faster is cheaper)  -> PORT_COST[1000]={fast_cost}")

    # --- accumulate() adds the cost of the port a BPDU arrived ON, not the sending port ---
    root = BridgeId(priority=100, mac="00:00:00:00:00:0a")
    path_at_root = PathToRoot(root_path_cost=0, neighbor_bridge=root, neighbor_port_id=1)
    one_hop = accumulate(path_at_root, ingress_speed_mbps=100)
    marker = "OK" if one_hop == 19 else "NG"
    print(f"[{marker}] accumulate adds ingress cost (100Mb) -> root_path_cost={one_hop}")

    two_hops = accumulate(PathToRoot(root_path_cost=one_hop, neighbor_bridge=root, neighbor_port_id=1), ingress_speed_mbps=10000)
    marker = "OK" if two_hops == 21 else "NG"
    print(f"[{marker}] second hop adds its OWN ingress cost -> root_path_cost={two_hops}")

    # --- better_path stage 1: lower root_path_cost wins outright ---
    neighbor_b = BridgeId(priority=200, mac="00:00:00:00:00:0b")
    neighbor_c = BridgeId(priority=200, mac="00:00:00:00:00:0b")
    cheap = PathToRoot(root_path_cost=19, neighbor_bridge=neighbor_b, neighbor_port_id=2)
    expensive = PathToRoot(root_path_cost=100, neighbor_bridge=neighbor_c, neighbor_port_id=1)
    stage1 = better_path(cheap, expensive)
    marker = "OK" if stage1 is True else "NG"
    print(f"[{marker}] stage 1: lower cost wins             -> better_path={stage1}")

    # --- better_path stage 2: cost tied, lower neighbor bridge ID wins ---
    lower_neighbor = BridgeId(priority=100, mac="00:00:00:00:00:01")
    higher_neighbor = BridgeId(priority=200, mac="00:00:00:00:00:02")
    via_lower = PathToRoot(root_path_cost=19, neighbor_bridge=lower_neighbor, neighbor_port_id=5)
    via_higher = PathToRoot(root_path_cost=19, neighbor_bridge=higher_neighbor, neighbor_port_id=1)
    stage2 = better_path(via_lower, via_higher)
    marker = "OK" if stage2 is True else "NG"
    print(f"[{marker}] stage 2: cost tied, lower neighbor id wins -> better_path={stage2}")

    # --- better_path stage 3: cost and neighbor bridge tied, lower neighbor port id wins ---
    same_neighbor = BridgeId(priority=100, mac="00:00:00:00:00:01")
    via_port_low = PathToRoot(root_path_cost=19, neighbor_bridge=same_neighbor, neighbor_port_id=1)
    via_port_high = PathToRoot(root_path_cost=19, neighbor_bridge=same_neighbor, neighbor_port_id=2)
    stage3 = better_path(via_port_low, via_port_high)
    marker = "OK" if stage3 is True else "NG"
    print(f"[{marker}] stage 3: bridge tied, lower port id wins    -> better_path={stage3}")


if __name__ == "__main__":
    main()
