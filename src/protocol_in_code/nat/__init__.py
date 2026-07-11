"""NAT/conntrack reading examples for the Protocol in Code course."""

from .five_tuple import (
    KNOWN_PROTOCOLS,
    MAX_PORT,
    MIN_PORT,
    FiveTuple,
    TupleValidity,
    reply_tuple,
    validate_tuple,
)
from .nat_loop import ToyNatBox, run_flow
from .ports import (
    EPHEMERAL_RANGE,
    AllocationOutcome,
    PortAllocator,
    allocate_port,
    release_port,
)
from .rewrite import Packet, RewriteKind, RewriteSpec, apply as apply_rewrite, apply_dnat, apply_snat
from .table import (
    ConntrackTable,
    MatchDirection,
    MatchResult,
    NatEntry,
    insert as table_insert,
    match as table_match,
    remove as table_remove,
)
from .timeout import EXPIRY_SECONDS, is_expired, sweep, touch

__all__ = [
    "EPHEMERAL_RANGE",
    "EXPIRY_SECONDS",
    "KNOWN_PROTOCOLS",
    "MAX_PORT",
    "MIN_PORT",
    "AllocationOutcome",
    "ConntrackTable",
    "FiveTuple",
    "MatchDirection",
    "MatchResult",
    "NatEntry",
    "Packet",
    "PortAllocator",
    "RewriteKind",
    "RewriteSpec",
    "ToyNatBox",
    "allocate_port",
    "apply_dnat",
    "apply_rewrite",
    "apply_snat",
    "is_expired",
    "release_port",
    "reply_tuple",
    "run_flow",
    "sweep",
    "table_insert",
    "table_match",
    "table_remove",
    "touch",
    "validate_tuple",
]
