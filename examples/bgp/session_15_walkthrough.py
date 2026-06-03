from protocol_in_code.bgp.export_policy import ExportPolicy, PeerType
from protocol_in_code.bgp.export_refresh import ExportTarget
from protocol_in_code.bgp.import_policy import ImportPolicy
from protocol_in_code.bgp.pipeline import PipelinePolicies
from protocol_in_code.bgp.policy import ValidationPolicy
from protocol_in_code.bgp.session import BGPSessionConfig
from protocol_in_code.bgp.speaker import ToyBGPSpeaker
from protocol_in_code.bgp.update import PathAttributes
from protocol_in_code.bgp.validation import VRP


def main() -> None:
    speaker = ToyBGPSpeaker(
        vrps=[VRP(prefix="203.0.113.0/24", max_length=24, origin_as=64496)],
        policies=PipelinePolicies(
            import_policy=ImportPolicy(),
            validation_policy=ValidationPolicy(reject_invalid=False),
            export_policy=ExportPolicy(local_as=64500),
        ),
    )
    speaker.add_neighbor(
        "upstream-a",
        BGPSessionConfig(peer_ip="198.51.100.1", peer_as=64501, local_as=64500, tcp_reachable=True),
    )
    speaker.add_export_target(
        ExportTarget(peer_id="customer-1", peer_type=PeerType.EBGP, policy=ExportPolicy(local_as=64500, next_hop_self=True))
    )
    speaker.add_neighbor(
        "upstream-b",
        BGPSessionConfig(peer_ip="198.51.100.2", peer_as=64502, local_as=64500, tcp_reachable=True),
    )
    speaker.add_export_target(
        ExportTarget(peer_id="upstream-shadow", peer_type=PeerType.EBGP, policy=ExportPolicy(local_as=64500, deny_prefixes=("203.0.113.0/24",)))
    )

    announce = speaker.receive_announce(
        "upstream-a",
        "203.0.113.0/24",
        PathAttributes(next_hop="198.51.100.1", local_pref=120, as_path=(64501, 64496), origin="igp"),
    )
    second = speaker.receive_announce(
        "upstream-b",
        "203.0.113.0/24",
        PathAttributes(next_hop="198.51.100.2", local_pref=100, as_path=(64502, 64496), origin="igp"),
    )
    withdraw = speaker.receive_withdraw("upstream-a", "203.0.113.0/24")
    peer_down = speaker.peer_down("upstream-b")

    print("announce_best:", announce.installed_paths["203.0.113.0/24"].next_hop if announce.installed_paths["203.0.113.0/24"] else None)
    print("second_best:", second.installed_paths["203.0.113.0/24"].next_hop if second.installed_paths["203.0.113.0/24"] else None)
    print("withdraw_best:", withdraw.installed_paths["203.0.113.0/24"].next_hop if withdraw.installed_paths["203.0.113.0/24"] else None)
    print("peer_down_best:", peer_down.installed_paths["203.0.113.0/24"])
    print("peer_down_state:", speaker.peers["upstream-b"].state.value)
    print("adj_rib_out_peers:", sorted(speaker.adj_rib_out.advertisements_by_peer.keys()))


if __name__ == "__main__":
    main()
