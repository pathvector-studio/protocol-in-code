from protocol_in_code.dns.cache import CacheEntry, ResolverCache
from protocol_in_code.dns.ttl import prune_expired, refresh_needed, remaining_ttl, served_ttl


def main() -> None:
    print("Session 05 walkthrough: TTL is a clock, not a config")
    print()

    entry = CacheEntry(records=("192.0.2.10",), stored_at=100, ttl=300)

    checks = (
        ("just stored", 100, 300),
        ("half life", 250, 150),
        ("one second left", 399, 1),
        ("exactly expired", 400, 0),
        ("long expired", 1000, 0),
    )
    for name, now, expected in checks:
        result = remaining_ttl(entry, now)
        marker = "OK" if result == expected else "NG"
        print(f"[{marker}] {name:20s} now={now:5d} -> remaining {result:4d} (expected {expected})")

    print()
    marker = "OK" if served_ttl(entry, 250) == 150 else "NG"
    print(f"[{marker}] served TTL shrinks with age  -> {served_ttl(entry, 250)} (original {entry.ttl})")

    marker = "OK" if refresh_needed(entry, 350, threshold=60) else "NG"
    print(f"[{marker}] refresh triggers near expiry -> {refresh_needed(entry, 350, threshold=60)}")
    marker = "OK" if not refresh_needed(entry, 150, threshold=60) else "NG"
    print(f"[{marker}] no refresh while fresh       -> {refresh_needed(entry, 150, threshold=60)}")

    print()
    cache = ResolverCache(
        entries={
            ("a.example.com", "A", "IN"): CacheEntry(("192.0.2.1",), stored_at=0, ttl=100),
            ("b.example.com", "A", "IN"): CacheEntry(("192.0.2.2",), stored_at=0, ttl=500),
            ("c.example.com", "A", "IN"): CacheEntry(("192.0.2.3",), stored_at=200, ttl=100),
        }
    )
    removed = prune_expired(cache, now=300)
    marker = "OK" if len(removed) == 2 and len(cache.entries) == 1 else "NG"
    print(f"[{marker}] prune at t=300 removed {len(removed)} entries, kept {len(cache.entries)}")
    for key in removed:
        print(f"     removed: {key[0]}")


if __name__ == "__main__":
    main()
