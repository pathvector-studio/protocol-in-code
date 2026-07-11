from protocol_in_code.meta.tristate import TristateDemo, demonstrate_all, why_not_bool


def main() -> None:
    print("Session 03 walkthrough: Three states beat two")
    print()

    rows = demonstrate_all()
    marker = "OK" if len(rows) == 4 else "NG"
    print(f"[{marker}] demonstrate_all() returns 4 rows    -> {len(rows)}")

    for row in rows:
        marker = "OK" if len(row.states) == 3 else "NG"
        print(f"[{marker}] {row.protocol:<6} states tuple has 3 entries -> {row.states}")

    meanings = {row.third_state_meaning for row in rows}
    marker = "OK" if len(meanings) == 4 else "NG"
    print(f"[{marker}] third_state_meaning strings all distinct -> {len(meanings)}")

    marker = "OK" if isinstance(rows[0], TristateDemo) else "NG"
    print(f"[{marker}] rows are TristateDemo instances      -> {type(rows[0]).__name__}")

    lesson = why_not_bool()
    marker = "OK" if lesson and ("two" in lesson and "flavors" in lesson) else "NG"
    print(f"[{marker}] why_not_bool() non-empty, mentions 'two'/'flavors' -> {bool(lesson)}")


if __name__ == "__main__":
    main()
