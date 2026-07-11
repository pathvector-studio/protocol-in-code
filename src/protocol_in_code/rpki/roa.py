"""Session thesis: a ROA is a permission slip.

A Route Origination Authorization is not infrastructure and it is not a
protocol message. It is three fields, signed by the prefix holder, saying:
"AS <origin_asn> may originate <prefix>, and may be as specific as
/<max_length> when doing so." Nothing more. The validator that reads it
(see validate.py) and the router that acts on the verdict (see policy.py)
are where the interesting behavior lives -- the ROA itself is just data.

Scope note: this toy only speaks IPv4. Real ROAs (and the RFC 6482 format)
cover IPv6 prefixes too; the address-family branching adds no new lesson
here, so it is left out on purpose.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from ipaddress import AddressValueError, IPv4Network, ip_network

IPV4_MAX_PREFIXLEN = 32


class RoaValidity(str, Enum):
    """Why a ROA object is or isn't a well-formed permission slip."""

    VALID = "valid"
    MALFORMED_PREFIX = "malformed_prefix"
    INVALID_MAX_LENGTH = "invalid_max_length"


@dataclass(frozen=True)
class Roa:
    """prefix + max_length + origin_asn: the whole permission slip, three fields."""

    prefix: str
    max_length: int
    origin_asn: int


def _parse_prefix(prefix: str) -> IPv4Network | None:
    """Parse the prefix string, returning None instead of raising on garbage input."""
    try:
        return ip_network(prefix)
    except (ValueError, AddressValueError):
        return None


def validate_roa(roa: Roa) -> RoaValidity:
    """A ROA is well-formed only if its prefix parses and its max_length is honest.

    max_length must be at least as specific as the prefix itself (you cannot
    authorize a /24 down to a /22 -- specificity only narrows) and it must not
    exceed the address family's longest possible prefix. This toy is IPv4-only,
    so that ceiling is 32.
    """
    network = _parse_prefix(roa.prefix)
    if network is None:
        return RoaValidity.MALFORMED_PREFIX

    if roa.max_length < network.prefixlen or roa.max_length > IPV4_MAX_PREFIXLEN:
        return RoaValidity.INVALID_MAX_LENGTH

    return RoaValidity.VALID
