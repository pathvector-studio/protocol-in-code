"""Four timestamps, two unknowns.

An NTP exchange hands back four timestamps: when the client sent (t1), when
the server received (t2), when the server replied (t3), and when the client
received the reply (t4). Hidden inside those four numbers are exactly two
unknowns worth solving for: the clock offset between client and server, and
the round-trip delay. RFC 5905 section 8 gives the closed-form solution.

Derivation. Let theta be the true offset (server clock minus client clock)
and let d_out, d_in be the one-way network delays out and back. Then:

    t2 = t1 + d_out + theta        (server receives; its clock reads ahead by theta)
    t4 = t3 + d_in - theta         (client receives; its clock reads behind by theta)

Two equations, but three unknowns (d_out, d_in, theta) if the delays differ.
NTP breaks the tie with an assumption: the path is symmetric, d_out = d_in = d.
Under that assumption, add the two equations and solve for theta:

    (t2 - t1) + (t4 - t3) = (d_out - d_in) + 2*theta = 2*theta   [since d_out = d_in]
    theta = ((t2 - t1) - (t4 - t3)) / 2 = ((t2 - t1) + (t3 - t4)) / 2

The two one-way estimates -- (t2 - t1) forward, (t4 - t3) backward -- each
carry both the network delay and the clock offset. Averaging them cancels
the delay term (it appears with opposite sign in the two directions) and
leaves the offset. That cancellation is exactly what breaks if the path is
NOT symmetric; see asymmetry.py for the honest accounting of that error.

Delay falls out of the same two equations: add both directions of travel
and subtract the time the server spent thinking:

    delay = (t4 - t1) - (t3 - t2)

This module, like tcp/seqnum.py, is pure arithmetic: no state, no I/O, just
the four numbers RFC 5905 asks for.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExchangeValidity(str, Enum):
    VALID = "Valid"
    MALFORMED = "Malformed"


@dataclass(frozen=True)
class Exchange:
    """The four NTP timestamps, in milliseconds (NTP itself uses 64-bit era
    timestamps; this course simplifies to plain integer milliseconds so the
    arithmetic reads like arithmetic).
    """

    t1: int  # client transmit time
    t2: int  # server receive time
    t3: int  # server transmit time
    t4: int  # client receive time


def validate_exchange(x: Exchange) -> ExchangeValidity:
    """A well-formed exchange has the server's send after its receive, and the
    client's receive after its own send. Either failing means the timestamps
    did not come from one coherent round trip.
    """
    if x.t4 < x.t1 or x.t3 < x.t2:
        return ExchangeValidity.MALFORMED
    return ExchangeValidity.VALID


def offset(x: Exchange) -> float:
    """RFC 5905 section 8: theta = ((t2 - t1) + (t3 - t4)) / 2."""
    return ((x.t2 - x.t1) + (x.t3 - x.t4)) / 2


def delay(x: Exchange) -> float:
    """RFC 5905 section 8: delay = (t4 - t1) - (t3 - t2)."""
    return (x.t4 - x.t1) - (x.t3 - x.t2)
