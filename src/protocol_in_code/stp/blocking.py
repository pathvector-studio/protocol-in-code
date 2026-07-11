"""Blocking is how loops die.

Ethernet has no TTL. A frame flooded onto a looped topology circulates
forever, doubling at every bridge that has more than one path to the same
segment, until the network melts down in a broadcast storm. STP's fix is not
clever routing - it is refusing to use some links at all. Every bridge
compares the BPDU it hears on a port against the BPDU it would itself send
there; if the received one is superior, the port has nothing useful to add
and goes BLOCKED.

Worked triangle: bridges A (root, lowest id), B, C, wired A-B, B-C, C-A, all
links equal cost - 19 per hop (100 Mbps, see path_cost.PORT_COST). Every
bridge's root_path_cost one hop from A is 19 (accumulate() charges the cost
on arrival, so what A transmits at cost 0 arrives everywhere as 19). Two
segments - A-B and B-C - have only one non-root speaker each, so nothing
there can outrank the BPDU that traces back to the root; both stay open.
The third segment, C-A, is where it gets interesting: A speaks on it
directly (root_id=A, cost=19-on-arrival, sender_bridge=A), and C would also
speak on it (root_id=A, cost=19, sender_bridge=C). Root tied, cost tied -
the tiebreak falls to sender_bridge, and A's own id beats C's. C's BPDU on
that segment loses the one comparison that was still open, so C's port to A
blocks - even though it is a direct link to the root. B keeps both its ports
forwarding because it never loses a tiebreak on either of its segments; the
loop breaks at exactly the one segment where a bridge's own re-advertisement
of the root's path collided head-on with the root speaking for itself, and
the root always wins that collision.
"""

from __future__ import annotations

from dataclasses import dataclass

from .root_election import BridgeId, bridge_id_lt


@dataclass(frozen=True)
class Bpdu:
    root_id: BridgeId
    root_path_cost: int
    sender_bridge: BridgeId
    sender_port: int


def bpdu_is_superior(a: Bpdu, b: Bpdu) -> bool:
    """Is `a` the better BPDU - the one a bridge should defer to over `b`?

    The canonical four-step comparison, each step an explicit branch:

    1. Lower root_id wins - a claim to a better root always wins outright.
    2. Root tied: lower root_path_cost wins - closer to the same root wins.
    3. Cost also tied: lower sender_bridge id wins - prefer the better-ranked speaker.
    4. Sender bridge also tied (same bridge heard on two of our ports): lower
       sender_port wins.
    """
    if a.root_id != b.root_id:
        return bridge_id_lt(a.root_id, b.root_id)

    if a.root_path_cost != b.root_path_cost:
        return a.root_path_cost < b.root_path_cost

    if a.sender_bridge != b.sender_bridge:
        return bridge_id_lt(a.sender_bridge, b.sender_bridge)

    return a.sender_port < b.sender_port


def should_block(heard: Bpdu, mine: Bpdu) -> bool:
    """A port blocks when the BPDU it hears beats the BPDU we would send there.

    If `heard` is superior to `mine`, someone else on that segment already
    speaks for a better (or equally good but higher-ranked) root path, so
    forwarding on this port would only create a loop back into a segment
    that's already served. If `mine` would win instead, we are the better
    speaker for that segment and the port stays open.
    """
    return bpdu_is_superior(heard, mine)
