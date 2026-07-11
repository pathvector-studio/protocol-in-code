from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

# STUN (RFC 5389) does one thing: the server reads the envelope of the packet
# that arrived and tells the sender what source address and port it saw. It
# never inspects the payload's claimed origin - the "mapped address" in the
# response IS the return address as observed from outside. Everything this
# track builds (nat_behavior.py, candidates.py) starts from that one fact.


@dataclass(frozen=True)
class BindingRequest:
    """What a client sends: "here is who I think I am." The server does not need to believe it."""

    from_ip: str
    from_port: int


@dataclass(frozen=True)
class BindingResponse:
    """What the server sends back: "here is who you actually looked like to me."""

    mapped_ip: str
    mapped_port: int


def stun_query(
    local_ip: str,
    local_port: int,
    nat_mapping: Callable[[str, int, str], tuple[str, int]] | None,
    server: str,
) -> BindingResponse:
    """Send a request through whatever sits between the client and the server, and report what arrived.

    With no NAT in the path, the mapping is the identity function - the server
    sees exactly the address the client sent from, and BindingResponse just
    echoes BindingRequest. A NAT in the path rewrites the envelope in flight,
    so the server sees something the client never chose. STUN cannot tell the
    difference between those two cases by itself - it only ever reports what
    it observed. The comparison against the client's own idea of itself is
    the caller's job (see behind_nat below).
    """
    request = BindingRequest(from_ip=local_ip, from_port=local_port)

    if nat_mapping is None:
        seen_ip, seen_port = request.from_ip, request.from_port
    else:
        seen_ip, seen_port = nat_mapping(request.from_ip, request.from_port, server)

    return BindingResponse(mapped_ip=seen_ip, mapped_port=seen_port)


def behind_nat(local: tuple[str, int], response: BindingResponse) -> bool:
    """The discovery IS the comparison: if the world saw something other than what you sent, something rewrote you."""
    return (response.mapped_ip, response.mapped_port) != local
