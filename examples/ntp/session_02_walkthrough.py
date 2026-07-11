from protocol_in_code.ntp.stratum import Candidate, STRATUM_MAX, STRATUM_UNSYNC, advertised_stratum, prefer, usable


def main() -> None:
    print("Session 02 walkthrough: Stratum is depth in a tree")
    print()

    one_hop = advertised_stratum(1)
    marker = "OK" if one_hop == 2 else "NG"
    print(f"[{marker}] upstream stratum 1 -> advertised     -> {one_hop}")

    at_cap = advertised_stratum(15)
    marker = "OK" if at_cap == STRATUM_UNSYNC else "NG"
    print(f"[{marker}] upstream stratum 15 -> capped at 16  -> {at_cap}")

    past_cap = advertised_stratum(20)
    marker = "OK" if past_cap == STRATUM_UNSYNC else "NG"
    print(f"[{marker}] upstream stratum 20 -> still capped  -> {past_cap}")

    edge_usable = usable(Candidate(server="edge", stratum=STRATUM_MAX, delay_ms=10.0))
    marker = "OK" if edge_usable else "NG"
    print(f"[{marker}] stratum 15 candidate is usable       -> {edge_usable}")

    unsync_unusable = usable(Candidate(server="unsync", stratum=STRATUM_UNSYNC, delay_ms=10.0))
    marker = "OK" if not unsync_unusable else "NG"
    print(f"[{marker}] stratum 16 candidate is not usable   -> {unsync_unusable}")

    close_shallow = Candidate(server="close", stratum=3, delay_ms=50.0)
    far_shallower = Candidate(server="far", stratum=2, delay_ms=5.0)
    winner = prefer(close_shallow, far_shallower)
    marker = "OK" if winner.server == "far" else "NG"
    print(f"[{marker}] lower stratum beats lower delay      -> {winner.server}")

    tie_a = Candidate(server="tie_a", stratum=2, delay_ms=50.0)
    tie_b = Candidate(server="tie_b", stratum=2, delay_ms=5.0)
    tie_winner = prefer(tie_a, tie_b)
    marker = "OK" if tie_winner.server == "tie_b" else "NG"
    print(f"[{marker}] equal stratum, lower delay wins      -> {tie_winner.server}")


if __name__ == "__main__":
    main()
