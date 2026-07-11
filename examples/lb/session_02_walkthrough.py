from protocol_in_code.lb.least_conn import ConnCounts, connection_closed, connection_opened, pick


def main() -> None:
    print("Session 02 walkthrough: Least connections is a counter")
    print()

    backends = ("s1", "s2", "s3")
    counts = ConnCounts()

    all_zero = pick(counts, backends)
    marker = "OK" if all_zero == "s1" else "NG"
    print(f"[{marker}] all counts zero, alpha tie  -> {all_zero}")

    connection_opened(counts, "s1")
    connection_opened(counts, "s1")
    after_two_on_s1 = pick(counts, backends)
    marker = "OK" if after_two_on_s1 == "s2" else "NG"
    print(f"[{marker}] s1 has 2, s2/s3 have 0      -> {after_two_on_s1}")

    connection_opened(counts, "s2")
    connection_opened(counts, "s3")
    still_tied_low = pick(counts, backends)
    marker = "OK" if still_tied_low == "s2" else "NG"
    print(f"[{marker}] s1=2 s2=1 s3=1, alpha tie   -> {still_tied_low}")

    connection_closed(counts, "s1")
    connection_closed(counts, "s1")
    shifted_back = pick(counts, backends)
    marker = "OK" if shifted_back == "s1" else "NG"
    print(f"[{marker}] closing s1 shifts pick back -> {shifted_back}")

    repeat_one = pick(counts, backends)
    repeat_two = pick(counts, backends)
    marker = "OK" if repeat_one == repeat_two else "NG"
    print(f"[{marker}] same state, same pick twice -> {repeat_one} == {repeat_two}")


if __name__ == "__main__":
    main()
