from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .hello import HelloCheckResult


class NeighborState(str, Enum):
    DOWN = "Down"
    INIT = "Init"
    TWO_WAY = "2-Way"
    EXSTART = "ExStart"
    EXCHANGE = "Exchange"
    LOADING = "Loading"
    FULL = "Full"


@dataclass(frozen=True)
class AdjacencyInputs:
    hello_accepted: bool
    saw_self: bool
    should_form_full_adjacency: bool
    database_description_ok: bool = True
    request_list_empty: bool = True
    retransmissions_cleared: bool = True


def inputs_from_hello(
    hello: HelloCheckResult,
    *,
    should_form_full_adjacency: bool,
    database_description_ok: bool = False,
    request_list_empty: bool = False,
    retransmissions_cleared: bool = False,
) -> AdjacencyInputs:
    return AdjacencyInputs(
        hello_accepted=hello.accepted,
        saw_self=hello.saw_self,
        should_form_full_adjacency=should_form_full_adjacency,
        database_description_ok=database_description_ok,
        request_list_empty=request_list_empty,
        retransmissions_cleared=retransmissions_cleared,
    )


def advance_on_hello(
    current: NeighborState,
    hello_accepted: bool,
    saw_self: bool,
    should_form_full_adjacency: bool,
) -> NeighborState:
    if not hello_accepted:
        return NeighborState.DOWN

    if not saw_self:
        return NeighborState.INIT

    if not should_form_full_adjacency:
        return NeighborState.TWO_WAY

    if current in {NeighborState.DOWN, NeighborState.INIT, NeighborState.TWO_WAY}:
        return NeighborState.EXSTART

    return current


def advance_neighbor_state(
    current: NeighborState,
    inputs: AdjacencyInputs,
) -> NeighborState:
    current = advance_on_hello(
        current,
        hello_accepted=inputs.hello_accepted,
        saw_self=inputs.saw_self,
        should_form_full_adjacency=inputs.should_form_full_adjacency,
    )

    if current in {NeighborState.DOWN, NeighborState.INIT, NeighborState.TWO_WAY}:
        return current

    if not inputs.database_description_ok:
        return NeighborState.EXSTART

    current = NeighborState.EXCHANGE
    if not inputs.request_list_empty:
        return NeighborState.LOADING
    if not inputs.retransmissions_cleared:
        return NeighborState.LOADING

    return NeighborState.FULL
