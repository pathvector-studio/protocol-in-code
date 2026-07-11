"""HA (VRRP + BFD) reading examples for the Protocol in Code course."""

from .bfd import BfdSession, BfdState
from .bfd import check_timeout as bfd_check_timeout
from .bfd import detection_time
from .bfd import on_packet as bfd_on_packet
from .failover_loop import ToyHaPair, run_failover
from .vrrp_election import PRIORITY_OWNER, VrrpRouter, elect, should_preempt
from .vrrp_timeout import ADVERTISEMENT_INTERVAL, BackupWatch, heartbeat, master_down_interval, master_is_down

__all__ = [
    "ADVERTISEMENT_INTERVAL",
    "BackupWatch",
    "BfdSession",
    "BfdState",
    "PRIORITY_OWNER",
    "ToyHaPair",
    "VrrpRouter",
    "bfd_check_timeout",
    "bfd_on_packet",
    "detection_time",
    "elect",
    "heartbeat",
    "master_down_interval",
    "master_is_down",
    "run_failover",
    "should_preempt",
]
