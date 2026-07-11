from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .stun import BindingResponse

# Candidates are gathered, not chosen: every address a host MIGHT be reachable
# at becomes a Candidate first, and only later (checklist.py) does anything
# decide which of them actually works. This module is pure enumeration plus
# one sorting formula.


class CandidateType(str, Enum):
    """RFC 8445 SS5.1.1: how a candidate's address was learned."""

    HOST = "Host"
    SERVER_REFLEXIVE = "ServerReflexive"
    RELAYED = "Relayed"


# RFC 8445 SS5.1.2.2 recommended type preferences: host wins over reflexive
# wins over relayed, because a direct route is cheaper than one that needs a
# STUN-visible mapping, and a relay is a last resort that costs a third party
# bandwidth.
TYPE_PREFERENCE: dict[CandidateType, int] = {
    CandidateType.HOST: 126,
    CandidateType.SERVER_REFLEXIVE: 100,
    CandidateType.RELAYED: 0,
}


@dataclass(frozen=True)
class Candidate:
    """One address the agent could be reached at, plus the base it was derived from."""

    ctype: CandidateType
    ip: str
    port: int
    base_ip: str
    base_port: int


def candidate_priority(ctype: CandidateType, local_pref: int, component_id: int = 1) -> int:
    """RFC 8445 SS5.1.2.1's literal formula - the only place preference among candidates gets decided."""
    return (2**24) * TYPE_PREFERENCE[ctype] + (2**8) * local_pref + (256 - component_id)


def gather(
    local_addr: tuple[str, int],
    stun_response: BindingResponse | None,
    turn_addr: tuple[str, int] | None,
) -> tuple[Candidate, ...]:
    """Enumerate every way in that might exist - judgment is someone else's problem.

    A host candidate always exists: it's just the local socket. A
    server-reflexive candidate exists only if a STUN query actually showed a
    different address than the local one - if there's no NAT in the path (or
    the observation happens to match), reflexive adds nothing new, so it is
    skipped rather than gathered as a duplicate. A relayed candidate exists
    only if a TURN allocation was actually made; gather() never allocates one
    itself, it only records that one is available.
    """
    local_ip, local_port = local_addr
    candidates: list[Candidate] = [
        Candidate(
            ctype=CandidateType.HOST,
            ip=local_ip,
            port=local_port,
            base_ip=local_ip,
            base_port=local_port,
        )
    ]

    if stun_response is not None and (stun_response.mapped_ip, stun_response.mapped_port) != local_addr:
        candidates.append(
            Candidate(
                ctype=CandidateType.SERVER_REFLEXIVE,
                ip=stun_response.mapped_ip,
                port=stun_response.mapped_port,
                base_ip=local_ip,
                base_port=local_port,
            )
        )

    if turn_addr is not None:
        relay_ip, relay_port = turn_addr
        candidates.append(
            Candidate(
                ctype=CandidateType.RELAYED,
                ip=relay_ip,
                port=relay_port,
                base_ip=local_ip,
                base_port=local_port,
            )
        )

    return tuple(candidates)
