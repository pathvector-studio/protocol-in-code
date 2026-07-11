from __future__ import annotations

from enum import Enum

# Demultiplexing is table lookup, nothing more. These two dicts are the
# entire "protocol stack" as far as a dispatcher is concerned: a number
# comes in, a name comes out, and the next parser is chosen by that name.
ETHERTYPES: dict[int, str] = {
    0x0800: "IPv4",
    0x0806: "ARP",
    0x86DD: "IPv6",
}

IP_PROTOCOLS: dict[int, str] = {
    1: "ICMP",
    6: "TCP",
    17: "UDP",
}


class LayerId(str, Enum):
    IPV4 = "IPv4"
    ARP = "ARP"
    IPV6 = "IPv6"
    ICMP = "ICMP"
    TCP = "TCP"
    UDP = "UDP"
    UNKNOWN = "Unknown"


def next_layer(ethertype: int) -> LayerId:
    """The ethertype names the layer above; an unmapped number just means we haven't taught it yet."""
    name = ETHERTYPES.get(ethertype)
    if name is None:
        return LayerId.UNKNOWN
    return LayerId(name)


def transport_protocol(proto_num: int) -> LayerId:
    """Same lookup, one layer up: the IP protocol number names the transport above it."""
    name = IP_PROTOCOLS.get(proto_num)
    if name is None:
        return LayerId.UNKNOWN
    return LayerId(name)
