"""Symmetry is an assumption.

offset.py derives theta = ((t2-t1)+(t3-t4))/2 by assuming the outbound and
return one-way delays are equal. This file is the honest sequel: it builds
exchanges from KNOWN ground truth, including a KNOWN asymmetry between the
forward and backward one-way times, and shows exactly what that assumption
costs when it is wrong.

Let d_f be the true forward (client-to-server) delay and d_b the true
backward (server-to-client) delay, with d_f != d_b. Re-deriving offset()
against the true offset theta (see offset.py for the symmetric case) gives:

    reported_offset = theta - (d_b - d_f) / 2

So the error (truth minus report) introduced by asymmetry is exactly
(d_b - d_f) / 2 -- half the gap between the two directions. Note the sign:
a slower return trip biases the reported offset downward (the client
thinks the server's clock is further behind than it is), because the extra
time on the return leg gets misread as clock skew rather than queuing.

The uncomfortable part is not the formula, it is what is NOT in the
exchange: t1, t2, t3, t4 alone never reveal d_f and d_b separately, only
their sum (the round-trip delay, computed in offset.delay). Two different
(d_f, d_b) pairs with the same sum produce the same four timestamps for a
given true offset. The protocol has no way to detect the asymmetry it
assumes away -- that is the thesis of this file.
"""

from __future__ import annotations

from .offset import Exchange


def true_offset_error(forward_ms: float, backward_ms: float) -> float:
    """How far offset()'s report drifts from the truth when the path is
    asymmetric: true_offset - reported_offset, which works out to exactly
    half the gap between the return delay and the forward delay.
    """
    return (backward_ms - forward_ms) / 2


def build_exchange(
    true_offset_ms: float,
    forward_ms: float,
    backward_ms: float,
    server_processing_ms: float,
    t1: int,
) -> Exchange:
    """Construct the four timestamps a real exchange would produce, given
    ground truth the protocol itself never gets to see: the true offset, the
    true one-way delays in each direction, and how long the server took to
    turn the packet around. This is a simulator, not a protocol step -- it
    exists so a walkthrough can compare offset()'s report to the truth it
    was built from.
    """
    t2 = t1 + forward_ms + true_offset_ms
    t3 = t2 + server_processing_ms
    t4 = t3 + backward_ms - true_offset_ms
    return Exchange(t1=round(t1), t2=round(t2), t3=round(t3), t4=round(t4))
