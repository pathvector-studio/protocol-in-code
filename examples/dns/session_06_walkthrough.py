from protocol_in_code.dns.cname import follow_cname


RECORDS = {
    ("app.example.com", "CNAME"): ("edge.example.net",),
    ("edge.example.net", "CNAME"): ("pop3.cdn.example",),
    ("pop3.cdn.example", "A"): ("203.0.113.7",),
    ("direct.example.com", "A"): ("192.0.2.20",),
    ("loop-a.example.com", "CNAME"): ("loop-b.example.com",),
    ("loop-b.example.com", "CNAME"): ("loop-a.example.com",),
    ("dangling.example.com", "CNAME"): ("nowhere.example.net",),
}


SCENARIOS = (
    (
        "direct A record, no chain",
        "direct.example.com",
        (True, "direct.example.com", 1, "answer"),
    ),
    (
        "two CNAME hops to an A",
        "app.example.com",
        (True, "pop3.cdn.example", 3, "answer"),
    ),
    (
        "dangling CNAME target",
        "dangling.example.com",
        (False, "nowhere.example.net", 2, "no answer and no CNAME"),
    ),
    (
        "CNAME loop",
        "loop-a.example.com",
        (False, "loop-b.example.com", 2, "CNAME loop detected"),
    ),
)


def main() -> None:
    print("Session 06 walkthrough: CNAME restarts the question")
    print()
    for name, qname, expected in SCENARIOS:
        result = follow_cname(qname, "A", RECORDS)
        got = (result.resolved, result.final_name, len(result.chain), result.stopped_because)
        marker = "OK" if got == expected else "NG"
        print(f"[{marker}] {name:28s} -> {' -> '.join(result.chain)}")
        print(f"     stopped: {result.stopped_because}, records: {result.records}")


if __name__ == "__main__":
    main()
