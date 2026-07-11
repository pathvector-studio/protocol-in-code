from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .five_tuple import FiveTuple


class RewriteKind(str, Enum):
    SNAT = "SNAT"
    DNAT = "DNAT"


@dataclass(frozen=True)
class Packet:
    """A packet on the wire, reduced to the tuple that routes it and a note standing in for its payload."""

    tuple: FiveTuple
    payload_note: str = ""


@dataclass(frozen=True)
class RewriteSpec:
    """What to rewrite and to what - a value object so a rule table can carry rewrites as data."""

    kind: RewriteKind
    ip: str
    port: int


def apply_snat(packet: Packet, new_src_ip: str, new_src_port: int) -> Packet:
    """Source NAT: swap the sender's own address as the packet leaves. The original packet is untouched."""
    rewritten = FiveTuple(
        protocol=packet.tuple.protocol,
        src_ip=new_src_ip,
        src_port=new_src_port,
        dst_ip=packet.tuple.dst_ip,
        dst_port=packet.tuple.dst_port,
    )
    return Packet(tuple=rewritten, payload_note=packet.payload_note)


def apply_dnat(packet: Packet, new_dst_ip: str, new_dst_port: int) -> Packet:
    """Destination NAT: swap where the packet is headed. Same shape as apply_snat, opposite field."""
    rewritten = FiveTuple(
        protocol=packet.tuple.protocol,
        src_ip=packet.tuple.src_ip,
        src_port=packet.tuple.src_port,
        dst_ip=new_dst_ip,
        dst_port=new_dst_port,
    )
    return Packet(tuple=rewritten, payload_note=packet.payload_note)


def apply(packet: Packet, spec: RewriteSpec) -> Packet:
    """Translation is a rewrite function: the router never mutates a packet, it substitutes a new one."""
    if spec.kind is RewriteKind.SNAT:
        return apply_snat(packet, spec.ip, spec.port)
    return apply_dnat(packet, spec.ip, spec.port)
