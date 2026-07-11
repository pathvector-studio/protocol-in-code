from protocol_in_code.ha.vrrp_election import PRIORITY_OWNER, VrrpRouter, elect, should_preempt


def main() -> None:
    print("Session 01 walkthrough: The highest priority speaks")
    print()

    owner = VrrpRouter(name="R1-owner", priority=PRIORITY_OWNER, primary_ip="192.0.2.1")
    high = VrrpRouter(name="R2-high", priority=200, primary_ip="192.0.2.2")
    low = VrrpRouter(name="R3-low", priority=100, primary_ip="192.0.2.3")

    # --- The address owner outranks every configured priority, no exceptions ---
    winner = elect((owner, high, low))
    marker = "OK" if winner is owner else "NG"
    print(f"[{marker}] owner (255) beats priority 200 -> winner={winner.name}")

    # --- Equal priority: the tiebreak is the higher primary IP, not name or order ---
    tie_low_ip = VrrpRouter(name="R4-tie-a", priority=150, primary_ip="192.0.2.10")
    tie_high_ip = VrrpRouter(name="R5-tie-b", priority=150, primary_ip="192.0.2.20")
    tie_winner = elect((tie_low_ip, tie_high_ip))
    marker = "OK" if tie_winner is tie_high_ip else "NG"
    print(f"[{marker}] equal priority, higher IP wins  -> winner={tie_winner.name}")

    # --- Order in the input tuple must not matter ---
    tie_winner_reversed = elect((tie_high_ip, tie_low_ip))
    marker = "OK" if tie_winner_reversed is tie_high_ip else "NG"
    print(f"[{marker}] tiebreak is order-independent    -> winner={tie_winner_reversed.name}")

    # --- should_preempt: higher priority candidate takes over, but only if preemption is on ---
    current_master = VrrpRouter(name="master", priority=100, primary_ip="192.0.2.30")
    better_candidate = VrrpRouter(name="candidate", priority=200, primary_ip="192.0.2.31")

    preempt_on = should_preempt(current_master, better_candidate, preempt_enabled=True)
    marker = "OK" if preempt_on is True else "NG"
    print(f"[{marker}] higher priority, preempt on      -> should_preempt={preempt_on}")

    preempt_off = should_preempt(current_master, better_candidate, preempt_enabled=False)
    marker = "OK" if preempt_off is False else "NG"
    print(f"[{marker}] higher priority, preempt off     -> should_preempt={preempt_off}")

    # --- A lower-priority candidate never preempts, even with preemption enabled ---
    worse_candidate = VrrpRouter(name="worse", priority=50, primary_ip="192.0.2.32")
    never_preempts = should_preempt(current_master, worse_candidate, preempt_enabled=True)
    marker = "OK" if never_preempts is False else "NG"
    print(f"[{marker}] lower priority never preempts    -> should_preempt={never_preempts}")


if __name__ == "__main__":
    main()
