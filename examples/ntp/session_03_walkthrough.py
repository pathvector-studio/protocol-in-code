from protocol_in_code.ntp.asymmetry import build_exchange, true_offset_error
from protocol_in_code.ntp.offset import offset


def main() -> None:
    print("Session 03 walkthrough: Symmetry is an assumption")
    print()

    symmetric = build_exchange(
        true_offset_ms=7, forward_ms=15, backward_ms=15, server_processing_ms=2, t1=1000
    )
    symmetric_report = offset(symmetric)
    marker = "OK" if symmetric_report == 7.0 else "NG"
    print(f"[{marker}] forward == backward -> report matches truth exactly -> {symmetric_report}")

    asymmetric = build_exchange(
        true_offset_ms=7, forward_ms=10, backward_ms=50, server_processing_ms=2, t1=1000
    )
    asymmetric_report = offset(asymmetric)
    marker = "OK" if asymmetric_report == -13.0 else "NG"
    print(f"[{marker}] forward=10ms backward=50ms -> report drifts -> {asymmetric_report}")

    error = true_offset_error(forward_ms=10, backward_ms=50)
    marker = "OK" if error == 20.0 else "NG"
    print(f"[{marker}] (backward-forward)/2 = (50-10)/2 -> error -> {error}")

    identity_holds = round(asymmetric_report + error, 6) == 7.0
    marker = "OK" if identity_holds else "NG"
    print(f"[{marker}] reported + error == truth -> {asymmetric_report} + {error} = {asymmetric_report + error}")

    marker = "OK" if error > 0 else "NG"
    print(f"[{marker}] slower return leg -> report reads MORE behind than truth -> error={error:+.1f}ms")

    print("[OK] nothing in t1..t4 alone reveals forward_ms and backward_ms separately -- "
          "only their sum, via offset.delay")


if __name__ == "__main__":
    main()
