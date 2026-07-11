from protocol_in_code.dns.query import DNSQuestion
from protocol_in_code.dns.resolver import ResolveSource, ToyResolver
from protocol_in_code.dns.walk import Zone


ZONES = {
    "": Zone(name="", delegations=("com", "net")),
    "com": Zone(name="com", delegations=("example.com",)),
    "net": Zone(name="net", delegations=("cdn.net",)),
    "example.com": Zone(
        name="example.com",
        answers={
            ("www.example.com", "A"): ("192.0.2.10",),
            ("app.example.com", "CNAME"): ("edge.cdn.net",),
        },
    ),
    "cdn.net": Zone(
        name="cdn.net",
        answers={
            ("edge.cdn.net", "A"): ("203.0.113.7",),
        },
    ),
}


def main() -> None:
    print("Session 08 walkthrough: Build the toy resolver loop")
    print()

    resolver = ToyResolver(zones=ZONES)

    steps = (
        (
            "invalid question is rejected",
            DNSQuestion(qname="bad..name"),
            ResolveSource.REJECTED,
            (),
            0,
        ),
        (
            "first lookup goes to the network",
            DNSQuestion(qname="www.example.com"),
            ResolveSource.NETWORK,
            ("192.0.2.10",),
            0,
        ),
        (
            "second lookup hits the cache",
            DNSQuestion(qname="www.example.com"),
            ResolveSource.CACHE,
            ("192.0.2.10",),
            10,
        ),
        (
            "CNAME crosses into another zone",
            DNSQuestion(qname="app.example.com"),
            ResolveSource.NETWORK,
            ("203.0.113.7",),
            0,
        ),
        (
            "unknown name fails after the walk",
            DNSQuestion(qname="ftp.example.com"),
            ResolveSource.FAILED,
            (),
            0,
        ),
        (
            "cache expires, back to the network",
            DNSQuestion(qname="www.example.com"),
            ResolveSource.NETWORK,
            ("192.0.2.10",),
            600,
        ),
    )

    for name, question, expected_source, expected_records, advance in steps:
        resolver.tick(advance)
        result = resolver.resolve(question)
        ok = result.source is expected_source and result.records == expected_records
        marker = "OK" if ok else "NG"
        print(f"[{marker}] {name:36s} -> {result.source.value:8s} {result.records}")
        for line in result.trace:
            print(f"     {line}")
        print()


if __name__ == "__main__":
    main()
