from __future__ import annotations

from dataclasses import dataclass, field

from .candidates import Candidate, CandidateType, gather
from .checklist import CandidatePair, ChecklistResult, Connectivity, form_checklist, run_checklist
from .stun import BindingResponse

# Build the toy connectivity check loop. ICE (RFC 8445) does not understand
# NATs - it does not classify them, does not predict which pairs will work.
# It gathers every candidate either side might be reachable at (candidates.py),
# sorts every possible pairing by a formula that prefers direct routes
# (checklist.py), and tries them in that order until one works. It is brute
# force with a priority order, and that is the whole trick.


@dataclass
class ToyIceAgent:
    """One side of the connection: a name, whatever candidates it gathered, and a trace of what it did."""

    name: str
    candidates: tuple[Candidate, ...] = ()
    trace: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class IceReport:
    nominated_pair: CandidatePair | None
    trace: tuple[str, ...]


def run_ice(agent_a: ToyIceAgent, agent_b: ToyIceAgent, reality: Connectivity) -> IceReport:
    """Drive the whole exchange: gather on both sides, cross the candidate lists, check in priority order, nominate.

    Nothing here knows in advance which pair will succeed - reality is only
    consulted inside check_pair, one pair at a time, in the order the
    checklist already fixed.
    """
    trace: list[str] = []

    trace.append(f"{agent_a.name} gathered: {[c.ctype.value for c in agent_a.candidates]}")
    trace.append(f"{agent_b.name} gathered: {[c.ctype.value for c in agent_b.candidates]}")
    trace.append(f"{agent_a.name} received {agent_b.name}'s candidates: {[c.ctype.value for c in agent_b.candidates]}")
    trace.append(f"{agent_b.name} received {agent_a.name}'s candidates: {[c.ctype.value for c in agent_a.candidates]}")

    pairs = form_checklist(agent_a.candidates, agent_b.candidates)
    trace.append(f"checklist formed, {len(pairs)} pairs, priority order: " + ", ".join(f"{p.local.ctype.value}x{p.remote.ctype.value}" for p in pairs))

    result: ChecklistResult = run_checklist(pairs, reality)

    checked_so_far = 0
    for pair in pairs:
        checked_so_far += 1
        if result.nominated is not None and pair is result.nominated:
            trace.append(f"check {checked_so_far}: {pair.local.ctype.value}x{pair.remote.ctype.value} -> SUCCEEDED (nominated)")
            break
        trace.append(f"check {checked_so_far}: {pair.local.ctype.value}x{pair.remote.ctype.value} -> FAILED")

    if result.nominated is None:
        trace.append("no pair succeeded - connectivity check exhausted the checklist")

    return IceReport(nominated_pair=result.nominated, trace=tuple(trace))


def scenario_direct_fails() -> IceReport:
    """Two hosts on different networks: HOSTxHOST cannot route, but STUN-learned reflexive candidates can.

    Both sides sit behind simple endpoint-independent NATs, so their
    server-reflexive candidates are stable, predictable public mappings - the
    easy case STUN alone was designed for.
    """
    a = ToyIceAgent(
        name="A",
        candidates=gather(
            local_addr=("10.0.1.5", 5000),
            stun_response=BindingResponse(mapped_ip="203.0.113.10", mapped_port=40000),
            turn_addr=None,
        ),
    )
    b = ToyIceAgent(
        name="B",
        candidates=gather(
            local_addr=("10.0.2.7", 6000),
            stun_response=BindingResponse(mapped_ip="203.0.113.20", mapped_port=50000),
            turn_addr=None,
        ),
    )

    reality = Connectivity(
        reachable_type_pairs=frozenset(
            {
                (CandidateType.SERVER_REFLEXIVE.value, CandidateType.SERVER_REFLEXIVE.value),
                (CandidateType.SERVER_REFLEXIVE.value, CandidateType.HOST.value),
                (CandidateType.HOST.value, CandidateType.SERVER_REFLEXIVE.value),
                (CandidateType.RELAYED.value, CandidateType.RELAYED.value),
            }
        )
    )

    report = run_ice(a, b, reality)
    assert report.nominated_pair is not None
    assert CandidateType.SERVER_REFLEXIVE in (report.nominated_pair.local.ctype, report.nominated_pair.remote.ctype)
    return report


def scenario_hard_nats() -> IceReport:
    """Both agents sit behind address-and-port-dependent NATs - nat_behavior.py's hardest personality, on both ends.

    A reflexive candidate learned by querying a STUN server predicts nothing
    about the mapping either NAT will produce toward the OTHER agent, because
    the other agent is a different destination than the STUN server was. So
    every reflexive pairing fails exactly like a host pairing would, and only
    a relay - a third party both sides can reach directly - closes the loop.
    """
    a = ToyIceAgent(
        name="A",
        candidates=gather(
            local_addr=("10.0.1.5", 5000),
            stun_response=BindingResponse(mapped_ip="203.0.113.10", mapped_port=40000),
            turn_addr=("198.51.100.1", 7000),
        ),
    )
    b = ToyIceAgent(
        name="B",
        candidates=gather(
            local_addr=("10.0.2.7", 6000),
            stun_response=BindingResponse(mapped_ip="203.0.113.20", mapped_port=50000),
            turn_addr=("198.51.100.2", 8000),
        ),
    )

    # Address-and-port-dependent NATs on both sides: nothing routes except
    # through the relay, which is reachable by anything because it is a
    # public server neither NAT rewrites in a destination-dependent way.
    reality = Connectivity(
        reachable_type_pairs=frozenset(
            {
                (CandidateType.RELAYED.value, CandidateType.RELAYED.value),
                (CandidateType.RELAYED.value, CandidateType.HOST.value),
                (CandidateType.HOST.value, CandidateType.RELAYED.value),
                (CandidateType.RELAYED.value, CandidateType.SERVER_REFLEXIVE.value),
                (CandidateType.SERVER_REFLEXIVE.value, CandidateType.RELAYED.value),
            }
        )
    )

    report = run_ice(a, b, reality)
    assert report.nominated_pair is not None
    assert CandidateType.RELAYED in (report.nominated_pair.local.ctype, report.nominated_pair.remote.ctype)
    failed_indices = [i for i, line in enumerate(report.trace) if line.endswith("FAILED")]
    succeeded_indices = [i for i, line in enumerate(report.trace) if "SUCCEEDED" in line]
    assert failed_indices, "expected failures traced before the eventual success"
    assert succeeded_indices and succeeded_indices[0] > failed_indices[-1], "success must be traced after the failures on the way down"
    return report
