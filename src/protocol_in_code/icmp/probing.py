from __future__ import annotations

from dataclasses import dataclass

from .message import IcmpMessage, QuotedPacket
from .ttl import HopOutcome, decrement_and_decide, expire
from .unreachable import make_port_unreachable


@dataclass(frozen=True)
class Hop:
    router_name: str
    responds: bool


@dataclass(frozen=True)
class Path:
    hops: tuple[Hop, ...]
    destination: str


@dataclass(frozen=True)
class ProbeResult:
    answerer: str | None
    message: IcmpMessage | None


def _quote_for(src_ip: str, dst_ip: str, dst_port: int) -> QuotedPacket:
    return QuotedPacket(
        src_ip=src_ip,
        dst_ip=dst_ip,
        protocol="UDP",
        src_port=33434,
        dst_port=dst_port,
    )


def probe(path: Path, ttl: int, dst_port: int) -> ProbeResult:
    """Time exceeded draws the map: send a doomed packet, see who confesses to killing it.

    Walk the path decrementing ttl once per hop. If ttl reaches 0 at hop
    i, that router is the one forced to answer TIME_EXCEEDED — unless it
    is configured silent, in which case the probe vanishes and NOTHING
    comes back. If ttl outlives every hop, the packet reaches the
    destination itself, which answers PORT_UNREACHABLE — classic UDP
    traceroute deliberately targets a high, unused port so the very last
    hop is guaranteed to error too. That inversion is the trick: the
    "error" is not a failure of the probe, it is the probe's success
    signal.
    """
    remaining = ttl
    for hop in path.hops:
        remaining, outcome = decrement_and_decide(remaining)
        if outcome is HopOutcome.EXPIRED:
            if not hop.responds:
                return ProbeResult(answerer=None, message=None)
            quoted = _quote_for(src_ip="probe-source", dst_ip=path.destination, dst_port=dst_port)
            return ProbeResult(answerer=hop.router_name, message=expire(quoted, hop.router_name))

    # ttl outlasted the whole path: the probe reached the destination.
    quoted = _quote_for(src_ip="probe-source", dst_ip=path.destination, dst_port=dst_port)
    return ProbeResult(answerer=path.destination, message=make_port_unreachable(quoted))
