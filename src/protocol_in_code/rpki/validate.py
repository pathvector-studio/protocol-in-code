"""Session thesis: three verdicts, not two.

Cross-reference: this is the same tri-state the learner met in
bgp/validation.py (session 04's ValidationState: VALID / INVALID /
NOT_FOUND), now built on the explicit prefix math from covering.py instead
of a single subnet_of()-and-max_length one-liner. The verdict names mirror
bgp/validation.py on purpose -- same shape, deeper machinery underneath.

The crucial state is NOT_FOUND. No covering ROA is not a verdict of
"denied" -- it means nobody has published a permission slip for this
address range at all, which describes most of the Internet even today.
Treating NOT_FOUND as a rejection would be treating silence as a lie.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .covering import find_covering_roas, within_max_length
from .roa import Roa


class OriginVerdict(str, Enum):
    """Mirrors bgp/validation.py's ValidationState: VALID / INVALID / NOT_FOUND."""

    VALID = "valid"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


@dataclass(frozen=True)
class ValidationResult:
    verdict: OriginVerdict
    matched_roa: Roa | None
    reason: str


def validate_origin(roas: tuple[Roa, ...], announced_prefix: str, origin_asn: int) -> ValidationResult:
    """Ask covering.py's two questions per ROA, then classify the outcome into three verdicts."""
    covering_roas = find_covering_roas(roas, announced_prefix)

    if not covering_roas:
        return ValidationResult(
            verdict=OriginVerdict.NOT_FOUND,
            matched_roa=None,
            reason="no ROA covers this address range; absence of a ROA is not a denial",
        )

    for roa in covering_roas:
        if roa.origin_asn == origin_asn and within_max_length(announced_prefix, roa.max_length):
            return ValidationResult(
                verdict=OriginVerdict.VALID,
                matched_roa=roa,
                reason=f"AS{origin_asn} is authorized up to /{roa.max_length}",
            )

    # Covering ROAs exist but none validated the announcement. Distinguish
    # *why* for the operator: wrong origin AS vs. announced too specifically.
    right_asn_too_specific = [roa for roa in covering_roas if roa.origin_asn == origin_asn]
    if right_asn_too_specific:
        allowed = ", ".join(f"/{roa.max_length}" for roa in right_asn_too_specific)
        reason = f"AS{origin_asn} is a covering origin but announcement is more specific than allowed ({allowed})"
    else:
        origins = ", ".join(f"AS{roa.origin_asn}" for roa in covering_roas)
        reason = f"covering ROA(s) authorize {origins}, not AS{origin_asn}"

    return ValidationResult(
        verdict=OriginVerdict.INVALID,
        matched_roa=None,
        reason=reason,
    )
