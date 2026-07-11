from protocol_in_code.meta.silence import SilenceDemo, demonstrate_all, timescale_spread


def main() -> None:
    print("Session 04 walkthrough: Silence means failure, everywhere")
    print()

    rows = demonstrate_all()
    marker = "OK" if len(rows) == 4 else "NG"
    print(f"[{marker}] demonstrate_all() returns 4 rows       -> {len(rows)}")

    by_protocol = {row.protocol: row.detection_time for row in rows}
    expected = {"bfd": 150, "vrrp": 3609, "nat_udp": 30000, "tcp_keepalive": 7800000}
    for protocol, value in expected.items():
        marker = "OK" if by_protocol.get(protocol) == value else "NG"
        print(f"[{marker}] {protocol:<13} detection_time == {value:>9,}ms -> {by_protocol.get(protocol):,}")

    spread = timescale_spread()
    marker = "OK" if spread == (150, 7800000) else "NG"
    print(f"[{marker}] timescale_spread() == (150, 7800000)    -> {spread}")

    ratio = spread[1] / spread[0]
    marker = "OK" if ratio == 52000 else "NG"
    print(f"[{marker}] 7,800,000 / 150 = {ratio:,.0f}x spread (five orders of magnitude)")

    marker = "OK" if isinstance(rows[0], SilenceDemo) else "NG"
    print(f"[{marker}] rows are SilenceDemo instances          -> {type(rows[0]).__name__}")


if __name__ == "__main__":
    main()
