from __future__ import annotations

from enum import Enum

# Seconds, matching nat/timeout.py's EXPIRY_SECONDS - keepalive and conntrack expiry
# are being compared directly in this file, so they need to share a unit.
#
# The classic Linux defaults (net.ipv4.tcp_keepalive_time/intvl/probes):
#   - wait KEEPALIVE_IDLE seconds of silence before probing at all,
#   - then send a probe every KEEPALIVE_INTERVAL seconds,
#   - and give up as dead after KEEPALIVE_COUNT unanswered probes.
KEEPALIVE_IDLE = 7200        # 2 hours
KEEPALIVE_INTERVAL = 75
KEEPALIVE_COUNT = 9

# 7200 seconds predates NAT reality: it was tuned for an era of dedicated leased
# lines and always-on hosts, where a 2-hour check-in was already generous. See
# nat/timeout.py: a NAT's UDP mapping is reclaimed after 30 seconds of silence,
# and even its TCP mapping - despite having FIN/RST to work with - is often
# reclaimed by middleboxes well under an hour of idle time. A keepalive that only
# fires after 7200 seconds shows up to find the mapping already gone; the probe
# that was supposed to keep the path alive arrives too late to do so.


class KeepaliveVerdict(str, Enum):
    ALIVE = "Alive"
    PROBING = "Probing"
    DEAD = "Dead"


def probe_times(last_activity: int) -> tuple[int, ...]:
    """The clock times at which each of the KEEPALIVE_COUNT probes goes out, first idle then spaced."""
    first = last_activity + KEEPALIVE_IDLE
    return tuple(first + i * KEEPALIVE_INTERVAL for i in range(KEEPALIVE_COUNT))


def connection_verdict(last_activity: int, probe_replies: tuple[bool, ...], now: int) -> KeepaliveVerdict:
    """Read the connection's health off the probe schedule: still quiet, actively probing, or given up on.

    probe_replies holds one bool per probe sent so far (True = a reply came back), in
    the same order as probe_times() - as many entries as probes that have actually
    fired by `now`. A single False doesn't kill the connection; only KEEPALIVE_COUNT
    consecutive unanswered probes do, at which point the connection is declared DEAD
    at the moment the last probe's silence is confirmed.
    """
    times = probe_times(last_activity)

    if now < times[0]:
        return KeepaliveVerdict.ALIVE

    if any(probe_replies):
        return KeepaliveVerdict.ALIVE

    if len(probe_replies) >= KEEPALIVE_COUNT and now >= times[KEEPALIVE_COUNT - 1]:
        return KeepaliveVerdict.DEAD

    return KeepaliveVerdict.PROBING
