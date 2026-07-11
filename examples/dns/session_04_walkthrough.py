from protocol_in_code.dns.cache import CacheOutcome, ResolverCache, lookup, store
from protocol_in_code.dns.query import DNSQuestion


def main() -> None:
    print("Session 04 walkthrough: The cache answers first")
    print()

    cache = ResolverCache()
    question = DNSQuestion(qname="www.example.com")

    first = lookup(cache, question, now=0)
    marker = "OK" if first.outcome is CacheOutcome.MISS else "NG"
    print(f"[{marker}] empty cache               -> {first.outcome.value}")

    store(cache, question, ("192.0.2.10",), ttl=300, now=0)

    second = lookup(cache, question, now=10)
    marker = "OK" if second.outcome is CacheOutcome.HIT and second.records == ("192.0.2.10",) else "NG"
    print(f"[{marker}] after store, 10s later    -> {second.outcome.value} {second.records}")

    other_spelling = lookup(cache, DNSQuestion(qname="WWW.Example.COM."), now=10)
    marker = "OK" if other_spelling.outcome is CacheOutcome.HIT else "NG"
    print(f"[{marker}] different spelling        -> {other_spelling.outcome.value}")

    other_type = lookup(cache, DNSQuestion(qname="www.example.com", qtype="AAAA"), now=10)
    marker = "OK" if other_type.outcome is CacheOutcome.MISS else "NG"
    print(f"[{marker}] same name, AAAA           -> {other_type.outcome.value}")

    expired = lookup(cache, question, now=300)
    marker = "OK" if expired.outcome is CacheOutcome.EXPIRED else "NG"
    print(f"[{marker}] at exactly ttl seconds    -> {expired.outcome.value}")

    after_expiry = lookup(cache, question, now=301)
    marker = "OK" if after_expiry.outcome is CacheOutcome.MISS else "NG"
    print(f"[{marker}] expired entry was removed -> {after_expiry.outcome.value}")


if __name__ == "__main__":
    main()
