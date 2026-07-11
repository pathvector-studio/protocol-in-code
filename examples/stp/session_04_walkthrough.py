from protocol_in_code.stp.blocking import Bpdu, bpdu_is_superior, should_block
from protocol_in_code.stp.root_election import BridgeId


def main() -> None:
    print("Session 04 walkthrough: Blocking is how loops die")
    print()

    bridge_a = BridgeId(priority=4096, mac="00:00:00:00:00:0a")
    bridge_b = BridgeId(priority=32768, mac="00:00:00:00:00:0b")
    bridge_c = BridgeId(priority=32768, mac="00:00:00:00:00:0c")

    # --- Stage 1 decides: root_id differs, lower root wins outright ---
    claims_a_as_root = Bpdu(root_id=bridge_a, root_path_cost=19, sender_bridge=bridge_b, sender_port=1)
    claims_c_as_root = Bpdu(root_id=bridge_c, root_path_cost=0, sender_bridge=bridge_c, sender_port=1)
    stage1 = bpdu_is_superior(claims_a_as_root, claims_c_as_root)
    marker = "OK" if stage1 is True else "NG"
    print(f"[{marker}] stage 1 (root_id) decides            -> a-superior={stage1}")

    # --- Stage 2 decides: root tied, lower root_path_cost wins ---
    closer_to_root = Bpdu(root_id=bridge_a, root_path_cost=19, sender_bridge=bridge_b, sender_port=1)
    farther_from_root = Bpdu(root_id=bridge_a, root_path_cost=38, sender_bridge=bridge_c, sender_port=1)
    stage2 = bpdu_is_superior(closer_to_root, farther_from_root)
    marker = "OK" if stage2 is True else "NG"
    print(f"[{marker}] stage 2 (root_path_cost) decides      -> a-superior={stage2}")

    # --- Stage 3 decides: root and cost tied, lower sender_bridge id wins ---
    sender_is_b = Bpdu(root_id=bridge_a, root_path_cost=19, sender_bridge=bridge_b, sender_port=1)
    sender_is_c = Bpdu(root_id=bridge_a, root_path_cost=19, sender_bridge=bridge_c, sender_port=1)
    stage3 = bpdu_is_superior(sender_is_b, sender_is_c)
    marker = "OK" if stage3 is True else "NG"
    print(f"[{marker}] stage 3 (sender_bridge) decides        -> b-superior={stage3}")

    # --- Stage 4 decides: root, cost, and sender_bridge all tied, lower sender_port wins ---
    heard_on_port_1 = Bpdu(root_id=bridge_a, root_path_cost=19, sender_bridge=bridge_b, sender_port=1)
    heard_on_port_2 = Bpdu(root_id=bridge_a, root_path_cost=19, sender_bridge=bridge_b, sender_port=2)
    stage4 = bpdu_is_superior(heard_on_port_1, heard_on_port_2)
    marker = "OK" if stage4 is True else "NG"
    print(f"[{marker}] stage 4 (sender_port) decides          -> port1-superior={stage4}")

    # --- should_block in both directions on the same pair of BPDUs ---
    heard = Bpdu(root_id=bridge_a, root_path_cost=19, sender_bridge=bridge_a, sender_port=2)
    mine = Bpdu(root_id=bridge_a, root_path_cost=19, sender_bridge=bridge_c, sender_port=2)
    blocks = should_block(heard, mine)
    marker = "OK" if blocks is True else "NG"
    print(f"[{marker}] heard beats mine -> port blocks         -> should_block={blocks}")

    reverse = should_block(mine, heard)
    marker = "OK" if reverse is False else "NG"
    print(f"[{marker}] mine beats heard -> port stays open      -> should_block={reverse}")

    # --- The docstring's worked triangle: C's port to A, on segment seg-ca ---
    # A speaks directly on seg-ca: root=A, cost=0 at emission, +19 on arrival at C.
    a_direct = Bpdu(root_id=bridge_a, root_path_cost=19, sender_bridge=bridge_a, sender_port=2)
    # C's own re-advertisement on that same segment: root=A, cost=19 (C's cost to root), sender=C.
    c_readvertised = Bpdu(root_id=bridge_a, root_path_cost=19, sender_bridge=bridge_c, sender_port=2)
    triangle_collision = should_block(a_direct, c_readvertised)
    marker = "OK" if triangle_collision is True else "NG"
    print(f"[{marker}] triangle: C's port to A blocks          -> should_block={triangle_collision}")


if __name__ == "__main__":
    main()
