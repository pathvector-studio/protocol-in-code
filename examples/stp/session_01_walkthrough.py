from protocol_in_code.stp.root_election import DEFAULT_PRIORITY, BridgeId, bridge_id_lt, elect_root


def main() -> None:
    print("Session 01 walkthrough: The root is the lowest ID")
    print()

    # --- The oldest-switch accident: equal (default) priority, lowest MAC wins ---
    old_switch = BridgeId(priority=DEFAULT_PRIORITY, mac="00:00:00:00:00:01")
    new_switch = BridgeId(priority=DEFAULT_PRIORITY, mac="aa:bb:cc:dd:ee:ff")
    accident_winner = elect_root((old_switch, new_switch))
    marker = "OK" if accident_winner is old_switch else "NG"
    print(f"[{marker}] equal priority, lowest MAC wins   -> root={accident_winner.mac} (the accident)")

    # --- The override: an explicit low priority beats a low MAC at default priority ---
    chosen_root = BridgeId(priority=100, mac="ff:ff:ff:ff:ff:ff")
    accidental_candidate = BridgeId(priority=DEFAULT_PRIORITY, mac="00:00:00:00:00:01")
    override_winner = elect_root((chosen_root, accidental_candidate))
    marker = "OK" if override_winner is chosen_root else "NG"
    print(f"[{marker}] priority 100 beats default+low MAC -> root={override_winner.mac} (the override)")

    # --- bridge_id_lt in both directions: (priority, mac) tuple compare, lowest wins ---
    lower = BridgeId(priority=100, mac="00:00:00:00:00:02")
    higher = BridgeId(priority=200, mac="00:00:00:00:00:01")
    forward = bridge_id_lt(lower, higher)
    marker = "OK" if forward is True else "NG"
    print(f"[{marker}] lower priority is lt higher         -> bridge_id_lt={forward}")

    backward = bridge_id_lt(higher, lower)
    marker = "OK" if backward is False else "NG"
    print(f"[{marker}] higher priority is not lt lower      -> bridge_id_lt={backward}")

    # --- elect_root over three bridges: lowest (priority, mac) tuple wins, not order ---
    bridge_a = BridgeId(priority=32768, mac="00:00:00:00:00:0a")
    bridge_b = BridgeId(priority=4096, mac="00:00:00:00:00:0b")
    bridge_c = BridgeId(priority=32768, mac="00:00:00:00:00:0c")
    three_way = elect_root((bridge_a, bridge_b, bridge_c))
    marker = "OK" if three_way is bridge_b else "NG"
    print(f"[{marker}] elect_root over 3 bridges            -> root={three_way.mac}")


if __name__ == "__main__":
    main()
