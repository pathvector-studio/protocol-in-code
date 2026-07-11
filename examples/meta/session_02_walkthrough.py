from protocol_in_code.meta.election import ElectionDemo, demonstrate_all, the_inversion


def main() -> None:
    print("Session 02 walkthrough: Election is a comparison function, five times")
    print()

    rows = demonstrate_all()
    marker = "OK" if len(rows) == 5 else "NG"
    print(f"[{marker}] demonstrate_all() returns 5 rows   -> {len(rows)}")

    directions = {row.direction for row in rows}
    expected_directions = {"highest wins", "lowest wins"}
    marker = "OK" if directions == expected_directions else "NG"
    print(f"[{marker}] both directions present            -> {sorted(directions)}")

    for row in rows:
        marker = "OK" if row.winner != "" else "NG"
        print(f"[{marker}] {row.protocol:<4} winner non-empty ({row.direction:<12}) -> {row.winner!r}")

    marker = "OK" if isinstance(rows[0], ElectionDemo) else "NG"
    print(f"[{marker}] rows are ElectionDemo instances     -> {type(rows[0]).__name__}")

    inversion = the_inversion()
    marker = "OK" if "STP" in inversion and "VRRP" in inversion else "NG"
    print(f"[{marker}] the_inversion() names STP and VRRP  -> {'STP' in inversion and 'VRRP' in inversion}")


if __name__ == "__main__":
    main()
