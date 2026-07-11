from protocol_in_code.lb.hash_pick import pick, remap_fraction


def main() -> None:
    print("Session 03 walkthrough: Hashing keeps you on the same server")
    print()

    backends = ("s1", "s2", "s3", "s4")

    first_pick = pick(backends, "client-42")
    second_pick = pick(backends, "client-42")
    marker = "OK" if first_pick == second_pick else "NG"
    print(f"[{marker}] same key, same backend      -> {first_pick} == {second_pick}")

    sample_keys = tuple(f"client-{i}" for i in range(20))
    picks = {pick(backends, key) for key in sample_keys}
    marker = "OK" if len(picks) >= 2 else "NG"
    print(f"[{marker}] different keys spread       -> {len(picks)} distinct backends")

    backends_before = ("s1", "s2", "s3", "s4")
    backends_after = ("s1", "s2", "s3", "s4", "s5")
    remap_keys = tuple(f"client-{i}" for i in range(5000))
    fraction = remap_fraction(backends_before, backends_after, remap_keys)
    marker = "OK" if fraction > 0.5 else "NG"
    print(f"[{marker}] 4->5 backends remaps >0.5   -> {fraction:.3f}")
    print(f"     this problem is what session 04's ring fixes")


if __name__ == "__main__":
    main()
