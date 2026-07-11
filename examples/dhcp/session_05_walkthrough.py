from protocol_in_code.dhcp.leases import Lease
from protocol_in_code.dhcp.renewal import RenewalState, renewal_state, renewal_target, t1, t2


def main() -> None:
    print("Session 05 walkthrough: Renewal happens before the end")
    print()

    lease = Lease(ip="192.0.2.50", granted_at=0, duration=100)
    print(f"lease: granted_at=0 duration=100 -> t1={t1(lease)} (100 // 2) t2={t2(lease)} (100 * 7 // 8)")
    print()

    fresh = renewal_state(lease, now=10)
    marker = "OK" if fresh is RenewalState.FRESH else "NG"
    print(f"[{marker}] now=10, before t1              -> {fresh.value}")

    at_t1 = renewal_state(lease, now=t1(lease))
    marker = "OK" if at_t1 is RenewalState.RENEWING else "NG"
    print(f"[{marker}] now==t1 (100 // 2 == 50)         -> {at_t1.value}")

    at_t2 = renewal_state(lease, now=t2(lease))
    marker = "OK" if at_t2 is RenewalState.REBINDING else "NG"
    print(f"[{marker}] now==t2 (100 * 7 // 8 == 87)      -> {at_t2.value}")

    at_end = renewal_state(lease, now=100)
    marker = "OK" if at_end is RenewalState.EXPIRED else "NG"
    print(f"[{marker}] now==granted_at+duration          -> {at_end.value}")

    print()
    print("the who-do-you-ask table:")
    for state, expected in (
        (RenewalState.FRESH, "none"),
        (RenewalState.RENEWING, "granting-server"),
        (RenewalState.REBINDING, "any-server"),
        (RenewalState.EXPIRED, "none"),
    ):
        target = renewal_target(state)
        marker = "OK" if target == expected else "NG"
        print(f"[{marker}] {state.value:<10} -> {target}")


if __name__ == "__main__":
    main()
