from protocol_in_code.dns.failures import FailureKind, ServerAttempt, try_servers


SCENARIOS = (
    (
        "first server answers",
        (
            ServerAttempt(server="ns1", records=("192.0.2.10",)),
            ServerAttempt(server="ns2", records=("192.0.2.10",)),
        ),
        (FailureKind.ANSWERED, "ns1", 1),
    ),
    (
        "timeout, then answer",
        (
            ServerAttempt(server="ns1", timed_out=True),
            ServerAttempt(server="ns2", records=("192.0.2.10",)),
        ),
        (FailureKind.ANSWERED, "ns2", 2),
    ),
    (
        "servfail, then answer",
        (
            ServerAttempt(server="ns1", rcode="SERVFAIL"),
            ServerAttempt(server="ns2", records=("192.0.2.10",)),
        ),
        (FailureKind.ANSWERED, "ns2", 2),
    ),
    (
        "nxdomain stops the fallback",
        (
            ServerAttempt(server="ns1", rcode="NXDOMAIN"),
            ServerAttempt(server="ns2", records=("192.0.2.10",)),
        ),
        (FailureKind.NAME_ERROR, "ns1", 1),
    ),
    (
        "every server fails",
        (
            ServerAttempt(server="ns1", timed_out=True),
            ServerAttempt(server="ns2", rcode="SERVFAIL"),
            ServerAttempt(server="ns3", rcode="REFUSED"),
        ),
        (FailureKind.REFUSED, "", 3),
    ),
)


def main() -> None:
    print("Session 07 walkthrough: Failure has flavors")
    print()
    for name, attempts, expected in SCENARIOS:
        result = try_servers(attempts)
        got = (result.kind, result.answered_by, len(result.tried))
        marker = "OK" if got == expected else "NG"
        answered = result.answered_by or "(nobody)"
        print(
            f"[{marker}] {name:28s} -> {result.kind.value:10s} "
            f"answered_by={answered:8s} tried={len(result.tried)}"
        )


if __name__ == "__main__":
    main()
