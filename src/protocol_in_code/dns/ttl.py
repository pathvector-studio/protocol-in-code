from __future__ import annotations

from .cache import CacheEntry, ResolverCache, entry_is_expired


def remaining_ttl(entry: CacheEntry, now: int) -> int:
    """How much lifetime the entry has left at this moment. Never negative."""
    return max(0, entry.stored_at + entry.ttl - now)


def served_ttl(entry: CacheEntry, now: int) -> int:
    """The TTL a resolver hands to its client: the remaining time, not the original TTL."""
    return remaining_ttl(entry, now)


def prune_expired(cache: ResolverCache, now: int) -> tuple[tuple[str, str, str], ...]:
    """Remove every entry whose clock has run out. Returns the keys that were removed."""
    expired_keys = tuple(
        key for key, entry in cache.entries.items() if entry_is_expired(entry, now)
    )
    for key in expired_keys:
        del cache.entries[key]
    return expired_keys


def refresh_needed(entry: CacheEntry, now: int, threshold: int) -> bool:
    """Some resolvers refetch before expiry. The trigger is remaining time, not age."""
    return remaining_ttl(entry, now) <= threshold
