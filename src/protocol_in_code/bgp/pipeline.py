from __future__ import annotations

from dataclasses import dataclass, replace

from .best_path import PathCandidate, select_best_path
from .export_policy import ExportPolicy, PeerType, prepare_export
from .import_policy import ImportPolicy, apply_import_policy
from .policy import PolicyAction, ValidationPolicy, decide_route_policy
from .ribs import (
    AdjRIBIn,
    AdjRIBOut,
    LocRIB,
    candidate_from_attributes,
    install_best_path,
    remove_best_path,
    received_attributes_for_prefix,
    stage_advertisement,
    store_received_path,
    withdraw_staged_advertisement,
)
from .update import PathAttributes
from .validation import BGPRoute, VRP, ValidationState, validate_origin


@dataclass(frozen=True)
class PipelinePolicies:
    import_policy: ImportPolicy
    validation_policy: ValidationPolicy
    export_policy: ExportPolicy


@dataclass(frozen=True)
class PipelineResult:
    prefix: str
    received_validation_state: ValidationState
    received_action: PolicyAction
    candidate_count: int
    selected_path: PathCandidate | None
    selected_exported_path: PathCandidate | None


def origin_as_from_attributes(attributes: PathAttributes) -> int:
    if not attributes.as_path:
        return 0
    return attributes.as_path[-1]


def apply_policy_action(
    candidate: PathCandidate,
    action: PolicyAction,
) -> PathCandidate | None:
    if action is PolicyAction.REJECT:
        return None
    if action is PolicyAction.DEPRIORITIZE:
        lowered = max(0, candidate.local_pref - 50)
        return replace(candidate, local_pref=lowered)
    return candidate


def evaluate_candidate(
    prefix: str,
    attributes: PathAttributes,
    vrps: list[VRP],
    policies: PipelinePolicies,
) -> tuple[ValidationState, PolicyAction, PathCandidate | None]:
    route = BGPRoute(prefix=prefix, origin_as=origin_as_from_attributes(attributes))
    validation_state = validate_origin(route, vrps)
    raw_candidate = candidate_from_attributes(prefix, attributes)
    imported = apply_import_policy(raw_candidate, validation_state, policies.import_policy)
    if imported is None:
        return validation_state, PolicyAction.REJECT, None

    action = decide_route_policy(validation_state, policies.validation_policy)
    installed = apply_policy_action(imported, action)
    return validation_state, action, installed


def process_single_route(
    peer_id: str,
    prefix: str,
    attributes: PathAttributes,
    vrps: list[VRP],
    policies: PipelinePolicies,
    adj_rib_in: AdjRIBIn,
    loc_rib: LocRIB,
    adj_rib_out: AdjRIBOut,
    export_peer_id: str,
    export_peer_type: PeerType,
) -> PipelineResult:
    store_received_path(adj_rib_in, peer_id, prefix, attributes)

    validation_state, action, _ = evaluate_candidate(prefix, attributes, vrps, policies)

    installable_candidates: list[PathCandidate] = []
    for _, received_attributes in received_attributes_for_prefix(adj_rib_in, prefix):
        _, _, installable = evaluate_candidate(prefix, received_attributes, vrps, policies)
        if installable is not None:
            installable_candidates.append(installable)

    if not installable_candidates:
        remove_best_path(loc_rib, prefix)
        withdraw_staged_advertisement(adj_rib_out, export_peer_id, prefix)
        return PipelineResult(
            prefix=prefix,
            received_validation_state=validation_state,
            received_action=action,
            candidate_count=0,
            selected_path=None,
            selected_exported_path=None,
        )

    best = select_best_path(installable_candidates)
    install_best_path(loc_rib, best)
    exported = prepare_export(best, export_peer_type, policies.export_policy)
    if exported is not None:
        stage_advertisement(adj_rib_out, export_peer_id, exported)
    else:
        withdraw_staged_advertisement(adj_rib_out, export_peer_id, prefix)

    return PipelineResult(
        prefix=prefix,
        received_validation_state=validation_state,
        received_action=action,
        candidate_count=len(installable_candidates),
        selected_path=best,
        selected_exported_path=exported,
    )
