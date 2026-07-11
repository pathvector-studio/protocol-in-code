from protocol_in_code.lb.hash_pick import remap_fraction as hash_remap_fraction
from protocol_in_code.lb.ring import build_ring, pick, remap_fraction


def main() -> None:
    print("Session 04 walkthrough: The ring survives a server change")
    print()

    backends = ("s1", "s2", "s3", "s4")
    vnodes = 100

    ring = build_ring(backends, vnodes)
    first_pick = pick(ring, "client-42")
    second_pick = pick(ring, "client-42")
    marker = "OK" if first_pick == second_pick else "NG"
    print(f"[{marker}] same key, same backend       -> {first_pick} == {second_pick}")

    backends_before = ("s1", "s2", "s3", "s4")
    backends_after = ("s1", "s2", "s3", "s4", "s5")
    sample_keys = tuple(f"client-{i}" for i in range(5000))

    ring_fraction = remap_fraction(backends_before, backends_after, sample_keys, vnodes)
    marker = "OK" if ring_fraction < 0.35 else "NG"
    print(f"[{marker}] ring remaps on 4->5 growth    -> {ring_fraction:.3f} (<0.35)")

    hash_fraction = hash_remap_fraction(backends_before, backends_after, sample_keys)
    marker = "OK" if hash_fraction > 0.5 else "NG"
    print(f"[{marker}] hash-mod remaps on 4->5       -> {hash_fraction:.3f} (>0.5)")
    print(f"     same inputs, same question: {ring_fraction:.3f} vs {hash_fraction:.3f} keys remapped")

    shrink_before = ("s1", "s2", "s3", "s4")
    shrink_after = ("s1", "s2", "s3")
    ring_before = build_ring(shrink_before, vnodes)
    ring_after = build_ring(shrink_after, vnodes)
    shrink_keys = tuple(f"client-{i}" for i in range(2000))

    moved = {key for key in shrink_keys if pick(ring_before, key) != pick(ring_after, key)}
    moved_were_on_s4 = all(pick(ring_before, key) == "s4" for key in moved)
    marker = "OK" if moved and moved_were_on_s4 else "NG"
    print(f"[{marker}] removing s4 only moves s4's keys -> {len(moved)} keys moved, all formerly on s4")

    stable_key = next(key for key in shrink_keys if pick(ring_before, key) != "s4" and pick(ring_before, key) == pick(ring_after, key))
    marker = "OK" if pick(ring_before, stable_key) == pick(ring_after, stable_key) else "NG"
    print(f"[{marker}] a key not on s4 stays put      -> {stable_key} -> {pick(ring_after, stable_key)} both times")


if __name__ == "__main__":
    main()
