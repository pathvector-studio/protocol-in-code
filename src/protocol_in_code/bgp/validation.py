from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from ipaddress import IPv4Network, ip_network


class ValidationState(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


@dataclass(frozen=True)
class BGPRoute:
    prefix: str
    origin_as: int


@dataclass(frozen=True)
class VRP:
    prefix: str
    max_length: int
    origin_as: int


def _route_network(route: BGPRoute) -> IPv4Network:
    return ip_network(route.prefix)


def _vrp_network(vrp: VRP) -> IPv4Network:
    return ip_network(vrp.prefix)


def vrp_covers_route(route: BGPRoute, vrp: VRP) -> bool:
    route_net = _route_network(route)
    vrp_net = _vrp_network(vrp)
    return route_net.subnet_of(vrp_net) and route_net.prefixlen <= vrp.max_length


def validate_origin(route: BGPRoute, vrps: list[VRP]) -> ValidationState:
    covering_vrps = [vrp for vrp in vrps if vrp_covers_route(route, vrp)]
    if not covering_vrps:
        return ValidationState.NOT_FOUND

    if any(vrp.origin_as == route.origin_as for vrp in covering_vrps):
        return ValidationState.VALID

    return ValidationState.INVALID
