from protocol_in_code.rpki.covering import covers, find_covering_roas, within_max_length
from protocol_in_code.rpki.roa import Roa


def main() -> None:
    print("Session 02 walkthrough: Covering is prefix math")
    print()

    inside = covers("203.0.112.0/22", "203.0.113.0/24")
    marker = "OK" if inside is True else "NG"
    print(f"[{marker}] /24 inside a covering /22  -> {inside}")

    disjoint = covers("203.0.112.0/22", "198.51.100.0/24")
    marker = "OK" if disjoint is False else "NG"
    print(f"[{marker}] disjoint prefix             -> {disjoint}")

    exact = covers("203.0.113.0/24", "203.0.113.0/24")
    marker = "OK" if exact is True else "NG"
    print(f"[{marker}] exact same prefix           -> {exact}")

    at_boundary = within_max_length("203.0.113.0/24", 24)
    marker = "OK" if at_boundary is True else "NG"
    print(f"[{marker}] /24 within max_length 24    -> {at_boundary}")

    past_boundary = within_max_length("203.0.113.0/24", 23)
    marker = "OK" if past_boundary is False else "NG"
    print(f"[{marker}] /24 within max_length 23    -> {past_boundary}")

    roas = (
        Roa(prefix="203.0.112.0/22", max_length=24, origin_asn=65001),
        Roa(prefix="198.51.100.0/24", max_length=24, origin_asn=65010),
        Roa(prefix="203.0.113.0/24", max_length=24, origin_asn=65002),
    )
    covering = find_covering_roas(roas, "203.0.113.0/24")
    marker = "OK" if len(covering) == 2 else "NG"
    print(f"[{marker}] 3 roas, 1 disjoint          -> {len(covering)} covering")


if __name__ == "__main__":
    main()
