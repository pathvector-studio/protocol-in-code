from protocol_in_code.bgp.session import BGPSessionConfig, SessionState, establish_neighbor


SCENARIOS = (
    (
        "empty peer_ip",
        BGPSessionConfig(
            peer_ip="",
            peer_as=65001,
            local_as=65000,
            tcp_reachable=True,
        ),
        SessionState.IDLE,
    ),
    (
        "tcp not reachable",
        BGPSessionConfig(
            peer_ip="192.0.2.1",
            peer_as=65001,
            local_as=65000,
            tcp_reachable=False,
        ),
        SessionState.ACTIVE,
    ),
    (
        "invalid remote AS",
        BGPSessionConfig(
            peer_ip="192.0.2.1",
            peer_as=0,
            local_as=65000,
            tcp_reachable=True,
        ),
        SessionState.OPEN_SENT,
    ),
    (
        "open negotiation failed",
        BGPSessionConfig(
            peer_ip="192.0.2.1",
            peer_as=65001,
            local_as=65000,
            tcp_reachable=True,
            open_message_ok=False,
        ),
        SessionState.OPEN_SENT,
    ),
    (
        "keepalive missing",
        BGPSessionConfig(
            peer_ip="192.0.2.1",
            peer_as=65001,
            local_as=65000,
            tcp_reachable=True,
            keepalive_received=False,
        ),
        SessionState.OPEN_CONFIRM,
    ),
    (
        "session established",
        BGPSessionConfig(
            peer_ip="192.0.2.1",
            peer_as=65001,
            local_as=65000,
            tcp_reachable=True,
        ),
        SessionState.ESTABLISHED,
    ),
)


def main() -> None:
    print("Session 01 walkthrough: What a BGP neighbor needs")
    print()
    for name, config, expected in SCENARIOS:
        result = establish_neighbor(config)
        marker = "OK" if result is expected else "NG"
        print(f"[{marker}] {name:24s} -> {result.value:12s} (expected {expected.value})")


if __name__ == "__main__":
    main()
