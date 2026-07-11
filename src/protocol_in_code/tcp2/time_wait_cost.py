from __future__ import annotations

# TWO_MSL is the promise made in track 1 (src/protocol_in_code/tcp/teardown.py):
# every actively-closed connection lingers TWO_MSL ticks before its port is free
# again. This file prices that promise. Units here are the same abstract "ticks"
# TWO_MSL is expressed in (240, matching the toy course clock) and a rate in
# connections per tick - there is no wall-clock conversion, this is pure ratio
# arithmetic, same spirit as tcp/seqnum.py.
from ..tcp.teardown import TWO_MSL

# The kernel's ephemeral port range (RFC 6056 territory, Linux default ip_local_port_range
# starts around here): every outbound connection to the SAME remote (ip, port) needs a
# distinct local port, and TIME_WAIT holds that port hostage until it expires.
EPHEMERAL_PORTS = 65535 - 49152 + 1


def time_wait_slots(rate_per_tick: float) -> int:
    """At a steady connect rate, how many ports are parked in TIME_WAIT at any instant?

    A connection opened and closed at a steady rate spends TWO_MSL ticks sitting in
    TIME_WAIT after it closes. By Little's Law the number of connections "in flight"
    through that wait is just rate times how long each one stays: rate_per_tick * TWO_MSL.
    """
    return int(rate_per_tick * TWO_MSL)


def max_rate_to_one_destination(ports: int = EPHEMERAL_PORTS) -> float:
    """The headline number: how fast can you open-and-close connections to ONE peer before ports run dry?

    Every connection to the same (local_ip, remote_ip, remote_port) triple needs a local
    port that isn't already parked in TIME_WAIT from a previous connection to that same
    peer. With `ports` local ports to cycle through and each one locked up for TWO_MSL
    ticks after use, the sustainable rate is ports / TWO_MSL - roughly 16384 / 240,
    about 68 connections per second to one destination, before new connects start
    finding every port still in TIME_WAIT. Closing connections fast is not free: it is
    the thing that makes this ceiling low.
    """
    return ports / TWO_MSL


def connect_would_fail(active_time_wait: int, ports: int = EPHEMERAL_PORTS) -> bool:
    """If this many ports are already parked in TIME_WAIT, is there anything left to connect() with?"""
    return active_time_wait >= ports
