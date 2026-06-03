from protocol_in_code.bgp.events import (
    AnnounceEvent,
    PeerDownEvent,
    WithdrawEvent,
    process_announce_event,
    process_peer_down_event,
    process_withdraw_event,
)
from protocol_in_code.bgp.export_policy import ExportPolicy, PeerType
from protocol_in_code.bgp.export_refresh import ExportTarget
from protocol_in_code.bgp.import_policy import ImportPolicy
from protocol_in_code.bgp.pipeline import PipelinePolicies
from protocol_in_code.bgp.policy import ValidationPolicy
from protocol_in_code.bgp.peer_state import open_peer_session
from protocol_in_code.bgp.ribs import AdjRIBIn, AdjRIBOut, LocRIB
from protocol_in_code.bgp.session import BGPSessionConfig
from protocol_in_code.bgp.update import PathAttributes
from protocol_in_code.bgp.validation import VRP


def main() -> None:
    peers = {
        "upstream-a": open_peer_session(
            "upstream-a",
            BGPSessionConfig(peer_ip="198.51.100.1", peer_as=64501, local_as=64500, tcp_reachable=True),
        ),
        "upstream-b": open_peer_session(
            "upstream-b",
            BGPSessionConfig(peer_ip="198.51.100.2", peer_as=64502, local_as=64500, tcp_reachable=True),
        ),
    }
    export_targets = (
        ExportTarget(
            peer_id="customer-1",
            peer_type=PeerType.EBGP,
            policy=ExportPolicy(local_as=64500, next_hop_self=True),
        ),
    )
    adj_rib_in = AdjRIBIn()
    loc_rib = LocRIB()
    adj_rib_out = AdjRIBOut()
    vrps = [VRP(prefix="203.0.113.0/24", max_length=24, origin_as=64496)]
    policies = PipelinePolicies(
        import_policy=ImportPolicy(),
        validation_policy=ValidationPolicy(reject_invalid=False),
        export_policy=ExportPolicy(local_as=64500),
    )

    first = process_announce_event(
        AnnounceEvent(
            peer_id="upstream-a",
            prefix="203.0.113.0/24",
            attributes=PathAttributes(
                next_hop="198.51.100.1",
                local_pref=100,
                as_path=(64501, 64496),
                origin="igp",
            ),
        ),
        peers,
        adj_rib_in,
        loc_rib,
        adj_rib_out,
        export_targets,
        vrps,
        policies,
    )
    second = process_withdraw_event(
        WithdrawEvent(peer_id="upstream-a", prefix="203.0.113.0/24"),
        adj_rib_in,
        loc_rib,
        adj_rib_out,
        export_targets,
        vrps,
        policies,
    )
    third = process_announce_event(
        AnnounceEvent(
            peer_id="upstream-b",
            prefix="203.0.113.0/24",
            attributes=PathAttributes(
                next_hop="198.51.100.2",
                local_pref=100,
                as_path=(64502, 64496),
                origin="igp",
            ),
        ),
        peers,
        adj_rib_in,
        loc_rib,
        adj_rib_out,
        export_targets,
        vrps,
        policies,
    )
    fourth = process_peer_down_event(
        PeerDownEvent(peer_id="upstream-b"),
        peers,
        adj_rib_in,
        loc_rib,
        adj_rib_out,
        export_targets,
        vrps,
        policies,
    )

    print("announce_best:", first.best_paths["203.0.113.0/24"].next_hop if first.best_paths["203.0.113.0/24"] else None)
    print("withdraw_best:", second.best_paths["203.0.113.0/24"])
    print("reannounce_best:", third.best_paths["203.0.113.0/24"].next_hop if third.best_paths["203.0.113.0/24"] else None)
    print("peer_down_prefixes:", fourth.touched_prefixes)
    print("peer_down_exports:", [change.kind.value for change in fourth.export_changes])


if __name__ == "__main__":
    main()
