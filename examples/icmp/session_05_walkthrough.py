from protocol_in_code.icmp.probing import Hop, Path
from protocol_in_code.icmp.trace_loop import (
    DEFAULT_MAX_TTL,
    SILENT_MARKER,
    ToyTracer,
    demo_path_with_silent_hop,
    run_traceroute,
)
from protocol_in_code.icmp.unreachable import UnreachableCode


def main() -> None:
    print("Session 05 walkthrough: Build the toy traceroute loop")
    print()

    path = demo_path_with_silent_hop()
    tracer = ToyTracer()
    answerers = run_traceroute(tracer, path)

    marker = "OK" if answerers == ("r1", SILENT_MARKER, "r3", path.destination) else "NG"
    print(f"[{marker}] full run over the demo path -> {answerers}")

    silence_line = "ttl=2 -> * (no response)"
    marker = "OK" if silence_line in tracer.trace else "NG"
    print(f"[{marker}] trace records the ttl=2 silence -> {silence_line!r} in trace")

    marker = "OK" if len(answerers) < DEFAULT_MAX_TTL else "NG"
    print(f"[{marker}] loop stopped at PORT_UNREACHABLE, not max_ttl -> {len(answerers)} hops < {DEFAULT_MAX_TTL}")

    expected_tail = f"{path.destination} {UnreachableCode.PORT_UNREACHABLE.value}"
    marker = "OK" if tracer.trace[-1].endswith(expected_tail) else "NG"
    print(f"[{marker}] last trace line names the destination's unreachable -> {tracer.trace[-1]}")

    fully_responsive = Path(
        hops=(
            Hop(router_name="a1", responds=True),
            Hop(router_name="a2", responds=True),
        ),
        destination="10.0.0.50",
    )
    quiet_tracer = ToyTracer()
    quiet_answerers = run_traceroute(quiet_tracer, fully_responsive)

    marker = "OK" if SILENT_MARKER not in quiet_answerers else "NG"
    print(f"[{marker}] fully-responsive path has no '*' -> {quiet_answerers}")


if __name__ == "__main__":
    main()
