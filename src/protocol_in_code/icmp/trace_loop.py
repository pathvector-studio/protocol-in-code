from __future__ import annotations

from dataclasses import dataclass, field

from .message import IcmpType
from .probing import Hop, Path, probe
from .unreachable import UnreachableCode

DEFAULT_MAX_TTL = 30
SILENT_MARKER = "*"


@dataclass
class ToyTracer:
    trace: list[str] = field(default_factory=list)


def run_traceroute(tracer: ToyTracer, path: Path, max_ttl: int = DEFAULT_MAX_TTL) -> tuple[str, ...]:
    """Build the toy traceroute loop.

    Traceroute never asks anyone where the path goes. It has no query
    for that. Instead it makes every router confess by sending packets
    it knows are doomed at increasing ttl, then reading the wreckage:
    each TIME_EXCEEDED names one more hop, and the PORT_UNREACHABLE from
    the destination itself — the "error" that is actually a success
    signal — is what ends the loop.
    """
    answerers: list[str] = []

    for ttl in range(1, max_ttl + 1):
        result = probe(path, ttl, dst_port=33434)

        if result.answerer is None:
            answerers.append(SILENT_MARKER)
            tracer.trace.append(f"ttl={ttl} -> {SILENT_MARKER} (no response)")
            continue

        assert result.message is not None
        answerers.append(result.answerer)

        if result.message.icmp_type is IcmpType.TIME_EXCEEDED:
            tracer.trace.append(f"ttl={ttl} -> {result.answerer} TimeExceeded")
        else:
            tracer.trace.append(f"ttl={ttl} -> {result.answerer} {UnreachableCode.PORT_UNREACHABLE.value}")
            break

    return tuple(answerers)


def demo_path_with_silent_hop() -> Path:
    """Three hops, the middle one configured not to answer — a common real-world firewall behavior."""
    return Path(
        hops=(
            Hop(router_name="r1", responds=True),
            Hop(router_name="r2", responds=False),
            Hop(router_name="r3", responds=True),
        ),
        destination="10.0.0.99",
    )
