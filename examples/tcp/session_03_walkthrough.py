from protocol_in_code.tcp.seqnum import SEQ_SPACE, in_receive_window, seq_add, seq_le, seq_lt


def main() -> None:
    print("Session 03 walkthrough: Sequence numbers wrap around")
    print()

    near_top = SEQ_SPACE - 10
    wrapped = seq_add(near_top, 20)
    marker = "OK" if wrapped == 10 else "NG"
    print(f"[{marker}] seq_add wraps past 2**32    -> {near_top} + 20 = {wrapped}")

    # Plain '<' says near_top < wrapped is False (4294967286 < 10 is False) -- wrong on the ring.
    plain_lt_is_wrong = not (near_top < wrapped)
    correct_seq_lt = seq_lt(near_top, wrapped)
    marker = "OK" if plain_lt_is_wrong and correct_seq_lt else "NG"
    print(f"[{marker}] plain '<' wrong across wrap  -> plain says False, seq_lt says {correct_seq_lt}")

    # Ordinary case, well away from the wrap: plain '<' and seq_lt agree.
    ordinary_agree = (100 < 200) == seq_lt(100, 200)
    marker = "OK" if ordinary_agree and seq_lt(100, 200) else "NG"
    print(f"[{marker}] plain '<' and seq_lt agree   -> seq_lt(100, 200) = {seq_lt(100, 200)}")

    equal_not_lt = seq_lt(500, 500)
    marker = "OK" if equal_not_lt is False else "NG"
    print(f"[{marker}] a seq is never lt itself     -> seq_lt(500, 500) = {equal_not_lt}")

    equal_is_le = seq_le(500, 500)
    marker = "OK" if equal_is_le is True else "NG"
    print(f"[{marker}] but it is le itself          -> seq_le(500, 500) = {equal_is_le}")

    just_before_wrap_le = seq_le(near_top, wrapped)
    marker = "OK" if just_before_wrap_le is True else "NG"
    print(f"[{marker}] seq_le follows the wrap too  -> seq_le({near_top}, {wrapped}) = {just_before_wrap_le}")

    rcv_nxt = SEQ_SPACE - 5
    seq_after_wrap = seq_add(rcv_nxt, 8)
    inside_after_wrap = in_receive_window(seq_after_wrap, rcv_nxt, window=20)
    marker = "OK" if inside_after_wrap is True else "NG"
    print(f"[{marker}] receive window spans the wrap -> seq {seq_after_wrap} (past 0) accepted")

    outside_window = in_receive_window(seq_add(rcv_nxt, 25), rcv_nxt, window=20)
    marker = "OK" if outside_window is False else "NG"
    print(f"[{marker}] just past the window is out   -> offset 25 >= window 20")

    zero_window_only_exact = in_receive_window(rcv_nxt, rcv_nxt, window=0) and not in_receive_window(
        seq_add(rcv_nxt, 1), rcv_nxt, window=0
    )
    marker = "OK" if zero_window_only_exact else "NG"
    print(f"[{marker}] zero window accepts only rcv_nxt -> {zero_window_only_exact}")


if __name__ == "__main__":
    main()
