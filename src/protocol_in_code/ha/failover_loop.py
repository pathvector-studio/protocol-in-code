"""Build the toy failover loop.

Two detectors watch the same failure at two timescales. BFD (bfd.py) is
wired for millisecond-scale loss of reachability; VRRP's Master_Down_Interval
(vrrp_timeout.py) is the seconds-scale fallback that fires even if BFD were
never configured. A real HA pair runs both: BFD notices first and triggers
the failover early, VRRP's own timer is the safety net that would have caught
it anyway, just later. This file wires VrrpRouter + BackupWatch + BfdSession
together into the smallest pair that can demonstrate the gap between them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .bfd import BfdSession, BfdState, check_timeout, on_packet
from .vrrp_election import VrrpRouter, should_preempt
from .vrrp_timeout import BackupWatch, heartbeat, master_is_down


@dataclass
class ToyHaPair:
    """Two VRRP routers, each with a BFD session to the other, sharing one virtual IP."""

    master_router: VrrpRouter
    backup_router: VrrpRouter
    virtual_ip: str
    preempt_enabled: bool = True
    master_watch: BackupWatch = field(default_factory=lambda: BackupWatch(last_heard_at=0))
    bfd_on_backup: BfdSession = field(
        default_factory=lambda: BfdSession(
            local_state=BfdState.UP,
            remote_state_last_heard=BfdState.UP,
            detect_multiplier=3,
            interval_ms=50,
            last_packet_at=0,
        )
    )
    clock: int = 0
    current_owner: str = ""
    trace: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.current_owner:
            self.current_owner = self.master_router.name

    def tick(self, ms: int) -> None:
        """Advance the clock and re-evaluate both detectors against the new silence.

        BFD is checked first because it is the faster detector - if it has
        already declared the peer down, ownership has already flipped by the
        time VRRP's own timeout would fire. VRRP's timer keeps running
        regardless (it is the fallback that would have caught the failure on
        its own), so its arrival is still traced even when BFD got there
        first - that gap between the two trace timestamps IS the two-timescale
        point.
        """
        self.clock += ms

        bfd_was_up = self.bfd_on_backup.local_state is not BfdState.DOWN
        bfd_state = check_timeout(self.bfd_on_backup, self.clock)
        if bfd_state is BfdState.DOWN and bfd_was_up:
            self.trace.append(f"t={self.clock}ms: BFD detects peer down (detection_time reached)")
            if self.current_owner == self.master_router.name:
                self._promote(self.backup_router)

        vrrp_was_up = not master_is_down(self.master_watch, self.master_router.priority, self.clock - ms)
        if vrrp_was_up and master_is_down(self.master_watch, self.master_router.priority, self.clock):
            self.trace.append(
                f"t={self.clock}ms: VRRP master_down_interval elapsed (fallback detector, would promote on its own)"
            )
            if self.current_owner == self.master_router.name:
                self._promote(self.backup_router)

    def _promote(self, router: VrrpRouter) -> None:
        self.current_owner = router.name
        self.trace.append(f"t={self.clock}ms: {self.virtual_ip} now owned by {router.name}")

    def advertisement_received(self) -> None:
        """The master's VRRP advertisement (and its BFD keepalive) both land at once."""
        heartbeat(self.master_watch, self.clock)
        on_packet(self.bfd_on_backup, BfdState.UP, self.clock)

    def master_returns(self) -> None:
        """The original master comes back and sends an advertisement; preemption decides the rest."""
        self.advertisement_received()
        current = self.master_router if self.current_owner == self.master_router.name else self.backup_router
        if current.name == self.master_router.name:
            return
        if should_preempt(current, self.master_router, self.preempt_enabled):
            self.trace.append(f"t={self.clock}ms: preemption on -> {self.master_router.name} takes back {self.virtual_ip}")
            self._promote(self.master_router)
        else:
            self.trace.append(
                f"t={self.clock}ms: preemption off -> {current.name} keeps {self.virtual_ip}, {self.master_router.name} stays backup"
            )

    def who_owns(self, virtual_ip: str) -> str:
        if virtual_ip != self.virtual_ip:
            return ""
        return self.current_owner


def run_failover(pair: ToyHaPair) -> ToyHaPair:
    """Walk the pair through steady state, silent failure, BFD-first detection, and a master return.

    Each stage appends to pair.trace so the two-timescale gap between BFD
    (milliseconds) and VRRP (~3 * ADVERTISEMENT_INTERVAL seconds) is visible
    as concrete timestamps, not just prose.
    """
    pair.trace.append(f"t={pair.clock}ms: steady state, {pair.virtual_ip} owned by {pair.who_owns(pair.virtual_ip)}")

    # Master goes silent: no more advertisements, no more BFD packets.
    pair.trace.append(f"t={pair.clock}ms: master goes silent")

    # Advance in small steps past BOTH thresholds: BFD's short detection_time
    # crosses first, VRRP's much longer master_down_interval crosses later,
    # confirming the fallback detector would have caught the failure anyway.
    for _ in range(80):
        pair.tick(ms=50)

    # Master returns and re-advertises; preemption setting decides the rest.
    pair.master_returns()

    return pair
