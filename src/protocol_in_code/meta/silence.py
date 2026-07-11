"""Silence means failure, everywhere.

BFD, VRRP, TCP keepalive, and NAT conntrack all make the same inference:
absence of evidence, after a deadline, becomes evidence of absence. What
differs is only the deadline's scale - BFD tunes it in milliseconds to
catch a dead peer before an application notices, while a stock TCP
keepalive tunes it in hours because it predates NAT middleboxes even
existing. This file calls each package's real timing function and puts
the resulting numbers, in one shared unit, side by side.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..ha.bfd import BfdSession, BfdState, detection_time
from ..ha.vrrp_timeout import master_down_interval
from ..nat.timeout import EXPIRY_SECONDS
from ..tcp2.keepalive import KEEPALIVE_COUNT, KEEPALIVE_IDLE, KEEPALIVE_INTERVAL, probe_times

MS_PER_SECOND = 1000


@dataclass(frozen=True)
class SilenceDemo:
    protocol: str
    threshold_description: str
    detection_time: int
    """Detection time in milliseconds, so all four protocols share one unit."""


def demonstrate_all() -> tuple[SilenceDemo, ...]:
    rows: list[SilenceDemo] = []

    # --- BFD: detect_multiplier * interval_ms, natively milliseconds --------
    session = BfdSession(
        local_state=BfdState.UP,
        remote_state_last_heard=BfdState.UP,
        detect_multiplier=3,
        interval_ms=50,
        last_packet_at=0,
    )
    bfd_ms = detection_time(session)
    rows.append(SilenceDemo("bfd", "detect_multiplier(3) * interval_ms(50)", bfd_ms))

    # --- VRRP: master_down_interval(priority), natively milliseconds --------
    vrrp_ms = master_down_interval(priority=100)
    rows.append(SilenceDemo("vrrp", "3*advertisement_interval + skew, priority=100", vrrp_ms))

    # --- TCP keepalive: idle + interval*(count-1) until the last probe fires,
    # natively seconds - the moment probe_times()'s final entry lands.
    times = probe_times(last_activity=0)
    keepalive_ms = times[-1] * MS_PER_SECOND
    rows.append(
        SilenceDemo(
            "tcp_keepalive",
            f"idle({KEEPALIVE_IDLE}s) + interval({KEEPALIVE_INTERVAL}s) x {KEEPALIVE_COUNT - 1} probes",
            keepalive_ms,
        )
    )

    # --- NAT conntrack: per-protocol idle timeout, natively seconds ---------
    nat_udp_ms = EXPIRY_SECONDS["udp"] * MS_PER_SECOND
    rows.append(SilenceDemo("nat_udp", f"EXPIRY_SECONDS['udp'] = {EXPIRY_SECONDS['udp']}s", nat_udp_ms))

    return tuple(rows)


def timescale_spread() -> tuple[int, int]:
    """(min, max) detection time in milliseconds across all four silence-detectors.

    The punchline is the range itself: BFD's 150ms is tuned to catch a dead
    peer inside the time a human notices a stall, while stock TCP keepalive's
    default sits almost five orders of magnitude higher - tuned for an era of
    dedicated leased lines, long before NAT middleboxes routinely reclaimed
    idle mappings in under a minute (see nat/timeout.py).
    """
    values = tuple(row.detection_time for row in demonstrate_all())
    return (min(values), max(values))
