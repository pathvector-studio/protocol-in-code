from protocol_in_code.dns.query import DNSQuestion
from protocol_in_code.dns.walk import Zone, walk_from_root


ZONES = {
    "": Zone(
        name="",
        delegations=("com", "org"),
    ),
    "com": Zone(
        name="com",
        delegations=("example.com",),
    ),
    "org": Zone(
        name="org",
        delegations=(),
    ),
    "example.com": Zone(
        name="example.com",
        answers={
            ("www.example.com", "A"): ("192.0.2.10",),
            ("example.com", "MX"): ("mail.example.com",),
        },
    ),
}

BROKEN_ZONES = {
    "": Zone(name="", delegations=("com",)),
    "com": Zone(name="com", delegations=("example.com",)),
    # "example.com" is delegated but nobody actually serves it.
}


SCENARIOS = (
    (
        "three hops to an A record",
        ZONES,
        DNSQuestion(qname="www.example.com"),
        (True, "answer", (".", "com", "example.com")),
    ),
    (
        "MX at the zone apex",
        ZONES,
        DNSQuestion(qname="example.com", qtype="MX"),
        (True, "answer", (".", "com", "example.com")),
    ),
    (
        "no delegation for the name",
        ZONES,
        DNSQuestion(qname="www.example.org"),
        (False, "no answer and no matching delegation", (".", "org")),
    ),
    (
        "zone knows nothing about the name",
        ZONES,
        DNSQuestion(qname="ftp.example.com"),
        (False, "no answer and no matching delegation", (".", "com", "example.com")),
    ),
    (
        "delegation to a missing zone",
        BROKEN_ZONES,
        DNSQuestion(qname="www.example.com"),
        (False, "delegation points to a missing zone", (".", "com")),
    ),
)


def main() -> None:
    print("Session 02 walkthrough: The resolver walks down the tree")
    print()
    for name, zones, question, expected in SCENARIOS:
        result = walk_from_root(question, zones)
        got = (result.found, result.stopped_because, result.path)
        marker = "OK" if got == expected else "NG"
        print(f"[{marker}] {name:36s} -> {' -> '.join(result.path):28s} ({result.stopped_because})")


if __name__ == "__main__":
    main()
