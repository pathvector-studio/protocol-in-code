from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InterfaceHelloConfig:
    local_router_id: str
    area_id: str
    netmask: str
    hello_interval: int
    dead_interval: int


@dataclass(frozen=True)
class OSPFHelloPacket:
    source_router_id: str
    area_id: str
    netmask: str
    hello_interval: int
    dead_interval: int
    priority: int
    designated_router: str | None
    backup_designated_router: str | None
    neighbors: tuple[str, ...] = ()


@dataclass(frozen=True)
class HelloCheckResult:
    accepted: bool
    saw_self: bool
    reasons: tuple[str, ...]


def evaluate_hello(
    config: InterfaceHelloConfig,
    packet: OSPFHelloPacket,
) -> HelloCheckResult:
    reasons: list[str] = []

    if packet.source_router_id == config.local_router_id:
        reasons.append("router_id_loop")
    if packet.area_id != config.area_id:
        reasons.append("area_mismatch")
    if packet.netmask != config.netmask:
        reasons.append("netmask_mismatch")
    if packet.hello_interval != config.hello_interval:
        reasons.append("hello_interval_mismatch")
    if packet.dead_interval != config.dead_interval:
        reasons.append("dead_interval_mismatch")

    if reasons:
        return HelloCheckResult(
            accepted=False,
            saw_self=False,
            reasons=tuple(reasons),
        )

    saw_self = config.local_router_id in packet.neighbors
    return HelloCheckResult(
        accepted=True,
        saw_self=saw_self,
        reasons=(),
    )
