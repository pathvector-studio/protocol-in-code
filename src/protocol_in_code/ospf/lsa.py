from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LSAHeader:
    lsa_type: str
    lsa_id: str
    advertising_router: str
    sequence: int
    age: int = 0


@dataclass(frozen=True)
class LinkDescription:
    neighbor_router_id: str
    metric: int


@dataclass(frozen=True)
class StubNetwork:
    prefix: str
    metric: int


@dataclass(frozen=True)
class RouterLSA:
    header: LSAHeader
    area_id: str
    links: tuple[LinkDescription, ...] = ()
    stub_networks: tuple[StubNetwork, ...] = ()


def router_lsa_key(lsa: RouterLSA) -> tuple[str, str]:
    return (lsa.header.advertising_router, lsa.header.lsa_id)


def is_newer_lsa(candidate: RouterLSA, current: RouterLSA) -> bool:
    if candidate.header.sequence != current.header.sequence:
        return candidate.header.sequence > current.header.sequence
    return candidate.header.age < current.header.age

