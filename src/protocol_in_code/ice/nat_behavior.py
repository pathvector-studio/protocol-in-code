from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# NATs have personalities: RFC 4787 SS4.1 defines them by what changes the
# mapping a NAT hands out for the same internal (ip, port). This module reads
# a sequence of observed mappings toward different destinations and names the
# behavior those observations imply.


class MappingBehavior(str, Enum):
    """RFC 4787 SS4.1 terms, from most to least NAT-friendly for peer-to-peer."""

    ENDPOINT_INDEPENDENT = "EndpointIndependent"
    ADDRESS_DEPENDENT = "AddressDependent"
    ADDRESS_AND_PORT_DEPENDENT = "AddressAndPortDependent"


@dataclass(frozen=True)
class Observation:
    """One STUN-style probe: sent toward (dest_ip, dest_port), the NAT mapped it to (mapped_ip, mapped_port)."""

    dest_ip: str
    dest_port: int
    mapped_ip: str
    mapped_port: int


def classify_mapping(obs: tuple[Observation, ...]) -> MappingBehavior:
    """Walk the observations in order, widening the verdict only when the mapping actually changes.

    Same mapping no matter the destination -> endpoint-independent: one
    reflexive candidate works for every peer. Mapping changes when the
    destination IP changes -> address-dependent. Mapping changes even when
    only the destination PORT changes (same IP) -> address-and-port-dependent,
    the strictest personality: a mapping learned by probing one destination
    is worthless toward any other, including a different port on the same
    STUN server.

    Cross-reference: nat/nat_loop.py's ToyNatBox allocates one port per
    5-tuple (ports.py + table.py key on the full tuple), so every new
    destination - even a different port on the same peer - gets a fresh
    translated tuple. That toy NAT IS address-and-port-dependent. It is the
    hardest personality for peer-to-peer: a reflexive candidate gathered by
    querying one STUN server predicts nothing about the mapping a real peer
    will see, because the peer is a different (ip, port) than the STUN
    server was. ICE's answer to that (checklist.py, ice_loop.py) is to stop
    trusting predictions and just try every candidate pair.
    """
    mappings_by_dest_ip: dict[str, set[tuple[str, int]]] = {}
    for o in obs:
        mapping = (o.mapped_ip, o.mapped_port)
        mappings_by_dest_ip.setdefault(o.dest_ip, set()).add(mapping)

    # Narrowest check first: does the mapping ever change for the SAME
    # destination IP just because the destination port differed? That is the
    # strictest personality, so it wins regardless of what happens across IPs.
    if any(len(mappings) > 1 for mappings in mappings_by_dest_ip.values()):
        return MappingBehavior.ADDRESS_AND_PORT_DEPENDENT

    # Every dest_ip now maps to exactly one mapping. Does that mapping differ
    # across destination IPs?
    distinct_mappings = {next(iter(mappings)) for mappings in mappings_by_dest_ip.values()}
    if len(distinct_mappings) > 1:
        return MappingBehavior.ADDRESS_DEPENDENT

    return MappingBehavior.ENDPOINT_INDEPENDENT
