from __future__ import annotations

from dataclasses import dataclass, replace

from .best_path import PathCandidate
from .export_policy import ExportPolicy, PeerType, prepare_export
from .import_policy import ImportPolicy, apply_import_policy
from .policy import PolicyAction, ValidationPolicy, decide_route_policy
from .ribs import AdjRIBIn, AdjRIBOut, LocRIB, install_best_path, stage_advertisement, store_received_path
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
    validation_state: ValidationState
    action: PolicyAction
    installed_path: PathCandidate | None
    exported_path: PathCandidate | None


def candidate_from_attributes(prefix: str, attributes: PathAttributes) -> PathCandidate:
    origin_map = {
        "igp": 0,
        "egp": 1,
        "incomplete": 2,
    }
    return PathCandidate(
        prefix=prefix,
        next_hop=attributes.next_hop,
        local_pref=attributes.local_pref,
        as_path=attributes.as_path,
        origin_type=origin_map.get(attributes.origin.lower(), 2),
    )


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

    route = BGPRoute(prefix=prefix, origin_as=origin_as_from_attributes(attributes))
    validation_state = validate_origin(route, vrps)

    raw_candidate = candidate_from_attributes(prefix, attributes)
    imported = apply_import_policy(raw_candidate, validation_state, policies.import_policy)
    if imported is None:
        return PipelineResult(
            prefix=prefix,
            validation_state=validation_state,
            action=PolicyAction.REJECT,
            installed_path=None,
            exported_path=None,
        )

    action = decide_route_policy(validation_state, policies.validation_policy)
    installed = apply_policy_action(imported, action)
    if installed is None:
        return PipelineResult(
            prefix=prefix,
            validation_state=validation_state,
            action=action,
            installed_path=None,
            exported_path=None,
        )

    install_best_path(loc_rib, installed)
    exported = prepare_export(installed, export_peer_type, policies.export_policy)
    if exported is not None:
        stage_advertisement(adj_rib_out, export_peer_id, exported)

    return PipelineResult(
        prefix=prefix,
        validation_state=validation_state,
        action=action,
        installed_path=installed,
        exported_path=exported,
    )
