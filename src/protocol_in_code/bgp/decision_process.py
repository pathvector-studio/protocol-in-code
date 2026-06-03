from __future__ import annotations

from dataclasses import dataclass

from .best_path import PathCandidate, select_best_path
from .pipeline import PipelinePolicies, evaluate_candidate
from .policy import PolicyAction
from .ribs import AdjRIBIn, received_attributes_for_prefix
from .validation import ValidationState, VRP


@dataclass(frozen=True)
class CandidateDecision:
    peer_id: str
    validation_state: ValidationState
    action: PolicyAction
    installed_candidate: PathCandidate | None


def evaluate_prefix_candidates(
    adj_rib_in: AdjRIBIn,
    prefix: str,
    vrps: list[VRP],
    policies: PipelinePolicies,
) -> list[CandidateDecision]:
    decisions: list[CandidateDecision] = []
    for peer_id, attributes in received_attributes_for_prefix(adj_rib_in, prefix):
        validation_state, action, installed = evaluate_candidate(prefix, attributes, vrps, policies)
        decisions.append(
            CandidateDecision(
                peer_id=peer_id,
                validation_state=validation_state,
                action=action,
                installed_candidate=installed,
            )
        )
    return decisions


def select_best_installable_for_prefix(
    adj_rib_in: AdjRIBIn,
    prefix: str,
    vrps: list[VRP],
    policies: PipelinePolicies,
) -> PathCandidate | None:
    decisions = evaluate_prefix_candidates(adj_rib_in, prefix, vrps, policies)
    installable = [decision.installed_candidate for decision in decisions if decision.installed_candidate is not None]
    if not installable:
        return None
    return select_best_path(installable)
