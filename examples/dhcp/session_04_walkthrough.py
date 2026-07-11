from protocol_in_code.dhcp.leases import LeaseOutcome, LeaseTable, grant_lease, lookup_lease


def main() -> None:
    print("Session 04 walkthrough: A lease is a dict with an expiry")
    print()

    table = LeaseTable()
    mac = "AA:BB:CC:00:11:22"

    first = lookup_lease(table, mac, now=0)
    marker = "OK" if first.outcome is LeaseOutcome.MISS else "NG"
    print(f"[{marker}] empty table                 -> {first.outcome.value}")

    granted = grant_lease(table, mac, ip="192.0.2.50", duration=100, now=0)

    second = lookup_lease(table, mac, now=10)
    marker = "OK" if second.outcome is LeaseOutcome.HIT and second.lease is not None and second.lease.ip == granted.ip else "NG"
    print(f"[{marker}] after grant, 10s later      -> {second.outcome.value} {second.lease.ip if second.lease else None}")

    still_fresh = lookup_lease(table, mac, now=99)
    marker = "OK" if still_fresh.outcome is LeaseOutcome.HIT else "NG"
    print(f"[{marker}] one second before duration  -> {still_fresh.outcome.value}")

    expired = lookup_lease(table, mac, now=100)
    marker = "OK" if expired.outcome is LeaseOutcome.EXPIRED else "NG"
    print(f"[{marker}] at exactly granted_at+dur   -> {expired.outcome.value}")

    after_expiry = lookup_lease(table, mac, now=101)
    marker = "OK" if after_expiry.outcome is LeaseOutcome.MISS else "NG"
    print(f"[{marker}] the fourth appearance of this dict deletes on expiry -> {after_expiry.outcome.value}")

    other_mac = lookup_lease(table, "FF:FF:FF:FF:FF:FF", now=101)
    marker = "OK" if other_mac.outcome is LeaseOutcome.MISS else "NG"
    print(f"[{marker}] a MAC that was never granted -> {other_mac.outcome.value}")


if __name__ == "__main__":
    main()
