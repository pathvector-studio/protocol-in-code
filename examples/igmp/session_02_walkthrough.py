from protocol_in_code.igmp.membership import GroupTable, anyone_interested, join
from protocol_in_code.igmp.querier import (
    MEMBERSHIP_TIMEOUT,
    MembershipState,
    expire_silent,
    on_report,
    report_suppression,
)


def main() -> None:
    print("Session 02 walkthrough: Queries keep the set honest")
    print()

    table = GroupTable()
    state = MembershipState()

    join(table, "224.0.1.5", "host-a")
    on_report(state, "224.0.1.5", "host-a", now=0)

    just_before = expire_silent(state, table, now=MEMBERSHIP_TIMEOUT - 1)
    marker = "OK" if just_before == () and anyone_interested(table, "224.0.1.5") else "NG"
    print(f"[{marker}] one tick before timeout       -> expired={just_before}, still interested")

    at_timeout = expire_silent(state, table, now=MEMBERSHIP_TIMEOUT)
    marker = "OK" if at_timeout == (("224.0.1.5", "host-a"),) and not anyone_interested(table, "224.0.1.5") else "NG"
    print(f"[{marker}] exactly at timeout (interest-expires lineage: dns/cache.py, dhcp/leases.py) -> expired={at_timeout}")

    join(table, "224.0.1.5", "host-b")
    on_report(state, "224.0.1.5", "host-b", now=0)
    on_report(state, "224.0.1.5", "host-b", now=100)
    survived = expire_silent(state, table, now=100 + MEMBERSHIP_TIMEOUT - 1)
    marker = "OK" if survived == () and anyone_interested(table, "224.0.1.5") else "NG"
    print(f"[{marker}] re-reported host survives      -> expired={survived}")

    two_members = ("host-c", "host-d")
    responder = report_suppression(two_members)
    marker = "OK" if responder == "host-c" else "NG"
    print(f"[{marker}] report_suppression picks one, {len(two_members) - 1} message(s) saved -> responder={responder}")

    try:
        report_suppression(())
        marker = "NG"
    except ValueError:
        marker = "OK"
    print(f"[{marker}] report_suppression with nobody -> raises ValueError")


if __name__ == "__main__":
    main()
