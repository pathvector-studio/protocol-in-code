"""Toy RIP models for Protocol in Code."""

from .count_to_infinity import (
    PREFIX,
    CountResult,
    RoundSnapshot,
    simulate_count_to_infinity,
    simulate_with_split_horizon,
)
from .infinity import INFINITY, clamp_metric, is_unreachable, poison
from .route import RipRoute, RouteValidity, better, validate_route
from .speaker import ConvergenceReport, ToyRipSpeaker, converge
from .split_horizon import advertisable, advertisable_with_poison
from .update import RoutingTable, UpdateOutcome, process_advertisement

__all__ = [
    "INFINITY",
    "PREFIX",
    "ConvergenceReport",
    "CountResult",
    "RipRoute",
    "RoundSnapshot",
    "RouteValidity",
    "RoutingTable",
    "ToyRipSpeaker",
    "UpdateOutcome",
    "advertisable",
    "advertisable_with_poison",
    "better",
    "clamp_metric",
    "converge",
    "is_unreachable",
    "poison",
    "process_advertisement",
    "simulate_count_to_infinity",
    "simulate_with_split_horizon",
    "validate_route",
]
