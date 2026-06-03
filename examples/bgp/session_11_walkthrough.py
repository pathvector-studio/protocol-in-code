from protocol_in_code.bgp.peer_state import open_peer_session, receive_update_if_established
from protocol_in_code.bgp.ribs import AdjRIBIn
from protocol_in_code.bgp.session import BGPSessionConfig
from protocol_in_code.bgp.update import PathAttributes


def main() -> None:
    adj_rib_in = AdjRIBIn()
    blocked_peer = open_peer_session(
        "peer-a",
        BGPSessionConfig(
            peer_ip="198.51.100.1",
            peer_as=64501,
            local_as=64500,
            tcp_reachable=False,
        ),
    )
    ready_peer = open_peer_session(
        "peer-b",
        BGPSessionConfig(
            peer_ip="198.51.100.2",
            peer_as=64502,
            local_as=64500,
            tcp_reachable=True,
        ),
    )
    route = PathAttributes(
        next_hop="198.51.100.2",
        local_pref=100,
        as_path=(64502, 64496),
        origin="igp",
    )

    blocked = receive_update_if_established(adj_rib_in, blocked_peer, "203.0.113.0/24", route)
    accepted = receive_update_if_established(adj_rib_in, ready_peer, "203.0.113.0/24", route)

    print("blocked_before_established:", blocked)
    print("accepted_after_established:", accepted)
    print("stored_peers:", sorted(adj_rib_in.paths_by_peer.keys()))


if __name__ == "__main__":
    main()
