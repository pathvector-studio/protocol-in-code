from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .validation import ValidationState


class PolicyAction(str, Enum):
    ACCEPT = "accept"
    DEPRIORITIZE = "deprioritize"
    REJECT = "reject"


@dataclass(frozen=True)
class ValidationPolicy:
    reject_invalid: bool = False
    deprioritize_not_found: bool = False


def decide_route_policy(
    validation_state: ValidationState,
    policy: ValidationPolicy,
) -> PolicyAction:
    if validation_state is ValidationState.INVALID:
        if policy.reject_invalid:
            return PolicyAction.REJECT
        return PolicyAction.DEPRIORITIZE

    if validation_state is ValidationState.NOT_FOUND and policy.deprioritize_not_found:
        return PolicyAction.DEPRIORITIZE

    return PolicyAction.ACCEPT
