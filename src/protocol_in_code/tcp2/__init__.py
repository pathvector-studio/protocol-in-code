"""Operational TCP reading examples for the Protocol in Code course: what running TCP at scale costs."""

from .backlog import AckOutcome, ListenBacklog
from .backlog import SynOutcome as BacklogSynOutcome
from .backlog import app_accept, on_final_ack, on_syn
from .janitor_loop import Event, EventKind, ToyConnectionJanitor, run_day_in_the_life
from .keepalive import (
    KEEPALIVE_COUNT,
    KEEPALIVE_IDLE,
    KEEPALIVE_INTERVAL,
    KeepaliveVerdict,
    connection_verdict,
    probe_times,
)
from .nagle_delack import DELACK_TIMEOUT_MS, READ, Timeline
from .nagle_delack import simulate as simulate_nagle_delack
from .syn_cookies import (
    COUNTER_MASK,
    MSS_TABLE,
    CookieVerdict,
    VerifyResult,
    encode_cookie,
    verify_cookie,
)
from .time_wait_cost import (
    EPHEMERAL_PORTS,
    TWO_MSL,
    connect_would_fail,
    max_rate_to_one_destination,
    time_wait_slots,
)

__all__ = [
    "COUNTER_MASK",
    "DELACK_TIMEOUT_MS",
    "EPHEMERAL_PORTS",
    "KEEPALIVE_COUNT",
    "KEEPALIVE_IDLE",
    "KEEPALIVE_INTERVAL",
    "MSS_TABLE",
    "READ",
    "TWO_MSL",
    "AckOutcome",
    "BacklogSynOutcome",
    "CookieVerdict",
    "Event",
    "EventKind",
    "KeepaliveVerdict",
    "ListenBacklog",
    "Timeline",
    "ToyConnectionJanitor",
    "VerifyResult",
    "app_accept",
    "connect_would_fail",
    "connection_verdict",
    "encode_cookie",
    "max_rate_to_one_destination",
    "on_final_ack",
    "on_syn",
    "probe_times",
    "run_day_in_the_life",
    "simulate_nagle_delack",
    "time_wait_slots",
    "verify_cookie",
]
