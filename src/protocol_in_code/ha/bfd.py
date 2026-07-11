"""Three states, both directions.

BFD (RFC 5880) is silence-means-failure again (see vrrp_timeout.py) but at a
different scale and with a different question. VRRP silence answers "should
I become master?" over seconds; BFD silence answers "is my peer reachable at
all?" over milliseconds, independent of whichever protocol is riding on top
of it. Where VRRP infers absence from one direction (backup listens for
master), BFD's session state is negotiated in both directions at once - each
side reports what it last heard the other side say, and the local state
climbs only as far as the two sides currently agree on.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BfdState(str, Enum):
    DOWN = "Down"
    INIT = "Init"
    UP = "Up"


@dataclass
class BfdSession:
    local_state: BfdState
    remote_state_last_heard: BfdState
    detect_multiplier: int
    interval_ms: int
    last_packet_at: int


def on_packet(session: BfdSession, remote_state: BfdState, now: int) -> BfdState:
    """Advance local_state through RFC 5880 section 6.2's three-way handshake table.

    The table is a visible ordered branch, cheapest case first:
      DOWN + remote DOWN  -> INIT  (peer also sees no session; start negotiating)
      DOWN + remote INIT  -> UP    (peer is already trying to reach us; agree)
      INIT + remote INIT  -> UP    (both sides negotiating; agree)
      INIT + remote UP    -> UP    (peer already considers the session up; agree)
      anything else       -> local_state unchanged (remote hasn't caught up yet)
    """
    session.remote_state_last_heard = remote_state
    session.last_packet_at = now

    if session.local_state is BfdState.DOWN and remote_state is BfdState.DOWN:
        session.local_state = BfdState.INIT
    elif session.local_state is BfdState.DOWN and remote_state is BfdState.INIT:
        session.local_state = BfdState.UP
    elif session.local_state is BfdState.INIT and remote_state in (BfdState.INIT, BfdState.UP):
        session.local_state = BfdState.UP

    return session.local_state


def detection_time(session: BfdSession) -> int:
    """The silence budget: detect_multiplier control packets' worth of interval."""
    return session.detect_multiplier * session.interval_ms


def check_timeout(session: BfdSession, now: int) -> BfdState:
    """Silence for a full detection_time drops the session straight back to DOWN.

    No INIT stopover on the way down - loss of the peer is immediate and total,
    unlike VRRP's single graduated wait.
    """
    if now >= session.last_packet_at + detection_time(session):
        session.local_state = BfdState.DOWN
    return session.local_state
