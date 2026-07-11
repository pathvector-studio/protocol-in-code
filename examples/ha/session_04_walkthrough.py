from protocol_in_code.ha.failover_loop import ToyHaPair, run_failover
from protocol_in_code.ha.vrrp_election import VrrpRouter


def main() -> None:
    print("Session 04 walkthrough: Build the toy failover loop")
    print()

    master = VrrpRouter(name="R1-master", priority=254, primary_ip="192.0.2.1")
    backup = VrrpRouter(name="R2-backup", priority=100, primary_ip="192.0.2.2")

    # --- Run 1: preemption ON (the default) ---
    pair = ToyHaPair(master_router=master, backup_router=backup, virtual_ip="192.0.2.100")

    marker = "OK" if pair.who_owns("192.0.2.100") == "R1-master" else "NG"
    print(f"[{marker}] steady state, master owns the VIP -> owner={pair.who_owns('192.0.2.100')}")

    # Master goes silent; step the clock forward in the same 50ms increments
    # run_failover() uses, stopping right after BFD's detection_time crosses,
    # so who_owns() can be checked before VRRP or the master's return happen.
    pair.trace.append(f"t={pair.clock}ms: master goes silent")
    for _ in range(3):
        pair.tick(ms=50)

    bfd_line = next((line for line in pair.trace if "BFD detects peer down" in line), None)
    marker = "OK" if bfd_line is not None and "t=150ms" in bfd_line else "NG"
    print(f"[{marker}] BFD detects the outage at t=150ms  -> {bfd_line}")

    ownership_flip_line = next(
        (line for line in pair.trace if "now owned by R2-backup" in line), None
    )
    marker = "OK" if ownership_flip_line is not None and "t=150ms" in ownership_flip_line else "NG"
    print(f"[{marker}] ownership flips to backup at t=150ms -> {ownership_flip_line}")

    owner_after_bfd = pair.who_owns("192.0.2.100")
    marker = "OK" if owner_after_bfd == "R2-backup" else "NG"
    print(f"[{marker}] who_owns() confirms the flip        -> owner={owner_after_bfd}")

    # Finish the rest of run_failover()'s walk: remaining silence, then the master's return.
    for _ in range(77):
        pair.tick(ms=50)
    pair.master_returns()

    vrrp_line = next(
        (line for line in pair.trace if "VRRP master_down_interval elapsed" in line), None
    )
    marker = "OK" if vrrp_line is not None and "t=3050ms" in vrrp_line else "NG"
    print(f"[{marker}] VRRP fallback still fires, later     -> {vrrp_line}")

    # --- The two-timescale headline: both lines exist, and BFD's line comes first ---
    bfd_index = pair.trace.index(bfd_line) if bfd_line else -1
    vrrp_index = pair.trace.index(vrrp_line) if vrrp_line else -1
    marker = "OK" if bfd_index != -1 and vrrp_index != -1 and bfd_index < vrrp_index else "NG"
    print(
        f"[{marker}] BFD line precedes VRRP line in the trace "
        f"-> BFD@{bfd_index} before VRRP@{vrrp_index} (150ms vs 3050ms)"
    )

    # --- Master returns; preemption is on, so it takes back the VIP ---
    preempt_line = next((line for line in pair.trace if "preemption on" in line), None)
    marker = "OK" if preempt_line is not None and "R1-master takes back" in preempt_line else "NG"
    print(f"[{marker}] preempt_enabled=True -> master takes back -> {preempt_line}")

    final_owner_preempt_on = pair.who_owns("192.0.2.100")
    marker = "OK" if final_owner_preempt_on == "R1-master" else "NG"
    print(f"[{marker}] final owner with preemption on      -> owner={final_owner_preempt_on}")

    # --- Run 2: preemption OFF - the backup keeps ownership when the master returns ---
    pair_no_preempt = ToyHaPair(
        master_router=master, backup_router=backup, virtual_ip="192.0.2.100", preempt_enabled=False
    )
    run_failover(pair_no_preempt)

    no_preempt_line = next(
        (line for line in pair_no_preempt.trace if "preemption off" in line), None
    )
    marker = "OK" if no_preempt_line is not None and "R2-backup keeps" in no_preempt_line else "NG"
    print(f"[{marker}] preempt_enabled=False -> backup keeps it -> {no_preempt_line}")

    final_owner_preempt_off = pair_no_preempt.who_owns("192.0.2.100")
    marker = "OK" if final_owner_preempt_off == "R2-backup" else "NG"
    print(f"[{marker}] final owner with preemption off     -> owner={final_owner_preempt_off}")


if __name__ == "__main__":
    main()
