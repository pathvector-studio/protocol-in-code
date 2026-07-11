"""Session thesis: policy decides what a verdict means.

Cross-reference: mirrors bgp/policy.py's PolicyAction / ValidationPolicy /
decide_route_policy shape (the learner met deprioritize-vs-reject there for
the same tri-state). This file renames ACCEPT's demoted sibling to
ACCEPT_LOWER_PREF to spell out that it is still an accept, just a
lower-preference one -- routers keep the route in the RIB, they just make it
lose tiebreaks.

A verdict is a fact about the world. What a router *does* with that fact is
a policy choice, and operators have made different choices at different
times:

- INVALID: strict shops REJECT outright. But accepting invalids and merely
  deprioritizing them was common practice during early RPKI deployment,
  when misconfigured ROAs could otherwise blackhole legitimate traffic.
- NOT_FOUND: most of the Internet still has no ROA at all. Rejecting
  NOT_FOUND routes wholesale would depeer most of the Internet, so the
  sane default is to accept (optionally deprioritized beneath VALID routes).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .validate import OriginVerdict


class PolicyAction(str, Enum):
    ACCEPT = "accept"
    ACCEPT_LOWER_PREF = "accept_lower_pref"
    REJECT = "reject"


@dataclass(frozen=True)
class RoutingPolicy:
    """Two booleans span the real operator spectrum from permissive to strict."""

    reject_invalid: bool
    lower_pref_not_found: bool


@dataclass(frozen=True)
class PolicyDecision:
    action: PolicyAction
    note: str


def apply_policy(verdict: OriginVerdict, policy: RoutingPolicy) -> PolicyDecision:
    """Turn a verdict plus a policy stance into a concrete forwarding decision."""
    if verdict is OriginVerdict.VALID:
        return PolicyDecision(PolicyAction.ACCEPT, "VALID routes are always accepted at full preference")

    if verdict is OriginVerdict.INVALID:
        if policy.reject_invalid:
            return PolicyDecision(PolicyAction.REJECT, "strict policy drops INVALID routes outright")
        return PolicyDecision(
            PolicyAction.ACCEPT_LOWER_PREF,
            "permissive policy keeps INVALID routes but deprioritizes them "
            "(common during early RPKI deployment, to avoid blackholing on ROA misconfiguration)",
        )

    # NOT_FOUND: no ROA exists for this range at all. Most of the Internet is
    # in this state, so rejecting it outright would break most of the Internet.
    if policy.lower_pref_not_found:
        return PolicyDecision(PolicyAction.ACCEPT_LOWER_PREF, "NOT_FOUND routes accepted but ranked beneath VALID")
    return PolicyDecision(PolicyAction.ACCEPT, "NOT_FOUND routes accepted at full preference (no ROA published)")
