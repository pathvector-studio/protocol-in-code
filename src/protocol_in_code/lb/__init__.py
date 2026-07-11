"""Load balancer reading examples for the Protocol in Code course."""

from .hash_pick import pick as hash_pick
from .hash_pick import remap_fraction as hash_remap_fraction
from .health import (
    FAIL_THRESHOLD,
    RISE_THRESHOLD,
    BackendHealth,
    HealthState,
    eligible,
    record_probe,
)
from .lb_loop import Strategy, ToyLoadBalancer, run_scenario
from .least_conn import ConnCounts
from .least_conn import connection_closed as lc_connection_closed
from .least_conn import connection_opened as lc_connection_opened
from .least_conn import pick as lc_pick
from .ring import build_ring
from .ring import pick as ring_pick
from .ring import remap_fraction as ring_remap_fraction
from .round_robin import RoundRobinState
from .round_robin import pick as rr_pick
from .round_robin import pick_weighted as rr_pick_weighted

__all__ = [
    "FAIL_THRESHOLD",
    "RISE_THRESHOLD",
    "BackendHealth",
    "ConnCounts",
    "HealthState",
    "RoundRobinState",
    "Strategy",
    "ToyLoadBalancer",
    "build_ring",
    "eligible",
    "hash_pick",
    "hash_remap_fraction",
    "lc_connection_closed",
    "lc_connection_opened",
    "lc_pick",
    "record_probe",
    "ring_pick",
    "ring_remap_fraction",
    "rr_pick",
    "rr_pick_weighted",
    "run_scenario",
]
