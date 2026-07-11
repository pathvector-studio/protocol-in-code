from protocol_in_code.dns.cache import CacheOutcome
from protocol_in_code.meta.expiring_state import ExpiryDemo, common_shape, demonstrate_all


def main() -> None:
    print("Session 01 walkthrough: The expiring dict, five times")
    print()

    rows = demonstrate_all(now_gap=0)
    marker = "OK" if len(rows) == 10 else "NG"
    print(f"[{marker}] demonstrate_all(0) returns 10 rows -> {len(rows)}")

    protocols = {row.protocol for row in rows}
    expected_protocols = {"dns", "tls", "dhcp", "nat", "igmp"}
    marker = "OK" if protocols == expected_protocols else "NG"
    print(f"[{marker}] all five protocols present       -> {sorted(protocols)}")

    for protocol in sorted(expected_protocols):
        before, after = (row for row in rows if row.protocol == protocol)
        marker = "OK" if before.outcome_name != after.outcome_name else "NG"
        print(f"[{marker}] {protocol:<4} before != after outcome -> {before.outcome_name} -> {after.outcome_name}")

    dns_before, dns_after = (row for row in rows if row.protocol == "dns")
    marker = "OK" if dns_before.outcome_name == CacheOutcome.HIT.value and dns_after.outcome_name == CacheOutcome.EXPIRED.value else "NG"
    print(f"[{marker}] dns pair matches CacheOutcome enum -> {dns_before.outcome_name} / {dns_after.outcome_name}")

    steps = common_shape()
    marker = "OK" if len(steps) == 4 else "NG"
    print(f"[{marker}] common_shape() has 4 steps         -> {len(steps)}")

    marker = "OK" if isinstance(rows[0], ExpiryDemo) else "NG"
    print(f"[{marker}] rows are ExpiryDemo instances       -> {type(rows[0]).__name__}")


if __name__ == "__main__":
    main()
