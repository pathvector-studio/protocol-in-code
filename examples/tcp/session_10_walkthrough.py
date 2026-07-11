from protocol_in_code.tcp.reset import ResetDisposition, on_reset
from protocol_in_code.tcp.segment import Segment
from protocol_in_code.tcp.teardown import CloseState, initiate_close


def main() -> None:
    print("Session 10 walkthrough: RST ends everything now")
    print()

    rcv_nxt = 1000
    window = 4096

    # An in-window RST closes an ESTABLISHED connection immediately, with no reply.
    in_window_rst = Segment(seq=rcv_nxt, ack=0, flags=frozenset({"RST"}))
    outcome = on_reset(CloseState.ESTABLISHED, in_window_rst, rcv_nxt, window)
    marker = "OK" if (
        outcome.disposition is ResetDisposition.ACCEPTED and outcome.new_state == "Closed"
    ) else "NG"
    print(f"[{marker}] in-window RST on ESTABLISHED -> {outcome.disposition.value} new_state={outcome.new_state}")

    # The very same RST, but its seq now falls outside the receive window: ignored, state untouched.
    out_of_window_rst = Segment(seq=rcv_nxt + window + 500, ack=0, flags=frozenset({"RST"}))
    outcome = on_reset(CloseState.ESTABLISHED, out_of_window_rst, rcv_nxt, window)
    marker = "OK" if (
        outcome.disposition is ResetDisposition.IGNORED and outcome.new_state is CloseState.ESTABLISHED
    ) else "NG"
    print(f"[{marker}] out-of-window RST ignored     -> {outcome.disposition.value} new_state={outcome.new_state.value}")

    # A segment without the RST flag is not a reset at all, regardless of window.
    data_segment = Segment(seq=rcv_nxt, ack=0, flags=frozenset(), payload_len=1)
    outcome = on_reset(CloseState.ESTABLISHED, data_segment, rcv_nxt, window)
    marker = "OK" if (
        outcome.disposition is ResetDisposition.NOT_A_RESET and outcome.new_state is CloseState.ESTABLISHED
    ) else "NG"
    print(f"[{marker}] non-RST segment                -> {outcome.disposition.value} new_state={outcome.new_state.value}")

    # A RST works the same way from a mid-teardown state too - no special casing per state.
    rst_during_finwait = Segment(seq=rcv_nxt, ack=0, flags=frozenset({"RST"}))
    outcome = on_reset(CloseState.FIN_WAIT_1, rst_during_finwait, rcv_nxt, window)
    marker = "OK" if (
        outcome.disposition is ResetDisposition.ACCEPTED and outcome.new_state == "Closed"
    ) else "NG"
    print(f"[{marker}] in-window RST during FIN_WAIT_1 -> {outcome.disposition.value} new_state={outcome.new_state}")

    # Contrast: teardown.py's FIN path needs initiate_close() to even leave ESTABLISHED, and never
    # reaches CLOSED without TIME_WAIT expiring first. RST needed one segment and zero replies.
    fin_state, _fin = initiate_close(seq=rcv_nxt)
    reset_outcome = on_reset(CloseState.ESTABLISHED, in_window_rst, rcv_nxt, window)
    marker = "OK" if (
        fin_state is CloseState.FIN_WAIT_1  # the FIN path: still three states and a wait from CLOSED
        and reset_outcome.new_state == "Closed"  # the RST path: already done
    ) else "NG"
    print(f"[{marker}] RST vs FIN: RST already Closed -> FIN path only reached {fin_state.value}")


if __name__ == "__main__":
    main()
