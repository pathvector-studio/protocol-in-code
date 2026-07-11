import copy

from protocol_in_code.tcp.congestion import CongestionPhase, CongestionState, on_ack, on_fast_retransmit, on_timeout, phase


def main() -> None:
    print("Session 07 walkthrough: cwnd is just a variable")
    print()

    state = CongestionState(cwnd=1, ssthresh=4)
    marker = "OK" if phase(state) is CongestionPhase.SLOW_START else "NG"
    print(f"[{marker}] starts in slow start          -> cwnd={state.cwnd} ssthresh={state.ssthresh} phase={phase(state).value}")

    cwnd_trace = [state.cwnd]
    for _ in range(3):
        on_ack(state)
        cwnd_trace.append(state.cwnd)
    marker = "OK" if cwnd_trace == [1, 2, 3, 4] else "NG"
    print(f"[{marker}] one MSS per ack while cwnd<ss -> cwnd trace={cwnd_trace}")

    marker = "OK" if state.cwnd == state.ssthresh and phase(state) is CongestionPhase.CONGESTION_AVOIDANCE else "NG"
    print(f"[{marker}] cwnd==ssthresh flips the phase -> cwnd={state.cwnd} ssthresh={state.ssthresh} phase={phase(state).value}")

    next_phase = on_ack(state)
    marker = "OK" if next_phase is CongestionPhase.CONGESTION_AVOIDANCE and state.cwnd == 4 and state.acks_in_round == 1 else "NG"
    print(f"[{marker}] avoidance counts acks, not cwnd yet -> cwnd={state.cwnd} acks_in_round={state.acks_in_round}")

    for _ in range(state.cwnd - state.acks_in_round - 1):
        on_ack(state)
    marker = "OK" if state.cwnd == 4 and state.acks_in_round == state.cwnd - 1 else "NG"
    print(f"[{marker}] avoidance needs cwnd acks     -> cwnd={state.cwnd} acks_in_round={state.acks_in_round}")

    on_ack(state)
    marker = "OK" if state.cwnd == 5 and state.acks_in_round == 0 else "NG"
    print(f"[{marker}] a full round grows by one MSS -> cwnd={state.cwnd} acks_in_round={state.acks_in_round}")

    shared_start = CongestionState(cwnd=10, ssthresh=20)

    after_timeout = copy.deepcopy(shared_start)
    on_timeout(after_timeout)
    marker = "OK" if after_timeout.cwnd == 1 and after_timeout.ssthresh == 5 else "NG"
    print(f"[{marker}] timeout collapses cwnd to 1   -> cwnd={after_timeout.cwnd} ssthresh={after_timeout.ssthresh}")

    after_fr = copy.deepcopy(shared_start)
    on_fast_retransmit(after_fr)
    marker = "OK" if after_fr.cwnd == 5 and after_fr.ssthresh == 5 else "NG"
    print(f"[{marker}] fast retransmit lands at ssthresh -> cwnd={after_fr.cwnd} ssthresh={after_fr.ssthresh}")

    marker = "OK" if after_timeout.ssthresh == after_fr.ssthresh and after_timeout.cwnd < after_fr.cwnd else "NG"
    print(f"[{marker}] same ssthresh, very different cwnd -> timeout cwnd={after_timeout.cwnd} vs fast-retransmit cwnd={after_fr.cwnd}")


if __name__ == "__main__":
    main()
