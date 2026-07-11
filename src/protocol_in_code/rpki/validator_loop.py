"""Session thesis: build the toy validator loop.

Everything so far has been pure functions on single ROAs and single
announcements. A real RPKI validator (routinator, rpki-client, etc.) is
just this loop run continuously: load the current ROA set, and for every
route the router hears, run covering -> validate -> policy and hand back
a decision. ToyValidator is that loop made small enough to read in one
sitting, plus a trace so every decision is explainable after the fact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .covering import find_covering_roas
from .policy import PolicyAction, PolicyDecision, RoutingPolicy, apply_policy
from .roa import Roa, RoaValidity, validate_roa
from .validate import OriginVerdict, ValidationResult, validate_origin


@dataclass(frozen=True)
class CheckResult:
    verdict: OriginVerdict
    action: PolicyAction
    trace_slice: tuple[str, ...]


@dataclass(frozen=True)
class TableReport:
    total: int
    verdict_counts: dict[OriginVerdict, int]
    action_counts: dict[PolicyAction, int]


@dataclass
class ToyValidator:
    """A minimal stand-in for a real RPKI validator: a ROA set, a policy stance, and a trace."""

    roas: tuple[Roa, ...] = ()
    policy: RoutingPolicy = field(default_factory=lambda: RoutingPolicy(reject_invalid=False, lower_pref_not_found=False))
    trace: list[str] = field(default_factory=list)

    def load_roas(self, roas: tuple[Roa, ...]) -> None:
        """Validate each candidate ROA via roa.py; malformed ones are skipped, not fatal."""
        accepted: list[Roa] = []
        for roa in roas:
            validity = validate_roa(roa)
            if validity is RoaValidity.VALID:
                accepted.append(roa)
                self.trace.append(f"load: accepted {roa.prefix} max/{roa.max_length} AS{roa.origin_asn}")
            else:
                self.trace.append(f"load: skipped {roa.prefix} max/{roa.max_length} AS{roa.origin_asn} ({validity.value})")
        self.roas = self.roas + tuple(accepted)

    def check(self, announced_prefix: str, origin_asn: int) -> CheckResult:
        """Run one announcement through covering -> validate -> policy, one trace line each."""
        start = len(self.trace)

        covering = find_covering_roas(self.roas, announced_prefix)
        self.trace.append(f"check {announced_prefix} AS{origin_asn}: {len(covering)} covering ROA(s)")

        result: ValidationResult = validate_origin(self.roas, announced_prefix, origin_asn)
        self.trace.append(f"check {announced_prefix} AS{origin_asn}: verdict={result.verdict.value} ({result.reason})")

        decision: PolicyDecision = apply_policy(result.verdict, self.policy)
        self.trace.append(f"check {announced_prefix} AS{origin_asn}: action={decision.action.value} ({decision.note})")

        return CheckResult(
            verdict=result.verdict,
            action=decision.action,
            trace_slice=tuple(self.trace[start:]),
        )


def demo_roas() -> tuple[Roa, ...]:
    """Four ROAs exercising every verdict: a clean VALID, a too-specific announcement,
    a wrong-ASN announcement, an uncovered range (NOT_FOUND), and one malformed ROA
    to exercise load_roas()'s skip path.
    """
    return (
        Roa(prefix="192.0.2.0/24", max_length=24, origin_asn=65001),
        Roa(prefix="198.51.100.0/22", max_length=23, origin_asn=65002),
        Roa(prefix="203.0.113.0/24", max_length=24, origin_asn=65003),
        Roa(prefix="not-a-prefix", max_length=24, origin_asn=65099),
    )


def evaluate_table(validator: ToyValidator, announcements: tuple[tuple[str, int], ...]) -> TableReport:
    """The route table sweep: run every announcement through the validator and tally verdicts."""
    verdict_counts: dict[OriginVerdict, int] = {verdict: 0 for verdict in OriginVerdict}
    action_counts: dict[PolicyAction, int] = {action: 0 for action in PolicyAction}

    for prefix, asn in announcements:
        result = validator.check(prefix, asn)
        verdict_counts[result.verdict] += 1
        action_counts[result.action] += 1

    return TableReport(
        total=len(announcements),
        verdict_counts=verdict_counts,
        action_counts=action_counts,
    )
