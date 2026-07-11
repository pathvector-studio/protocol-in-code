from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .query import DNSQuestion, question_key


class CacheOutcome(str, Enum):
    HIT = "Hit"
    MISS = "Miss"
    EXPIRED = "Expired"


@dataclass(frozen=True)
class CacheEntry:
    records: tuple[str, ...]
    stored_at: int
    ttl: int


@dataclass
class ResolverCache:
    entries: dict[tuple[str, str, str], CacheEntry] = field(default_factory=dict)


@dataclass(frozen=True)
class CacheLookup:
    outcome: CacheOutcome
    records: tuple[str, ...]


def entry_is_expired(entry: CacheEntry, now: int) -> bool:
    return now >= entry.stored_at + entry.ttl


def lookup(cache: ResolverCache, question: DNSQuestion, now: int) -> CacheLookup:
    """The cache answers first. Only a miss or an expiry sends the resolver to the network."""
    key = question_key(question)

    entry = cache.entries.get(key)
    if entry is None:
        return CacheLookup(CacheOutcome.MISS, ())

    if entry_is_expired(entry, now):
        del cache.entries[key]
        return CacheLookup(CacheOutcome.EXPIRED, ())

    return CacheLookup(CacheOutcome.HIT, entry.records)


def store(
    cache: ResolverCache,
    question: DNSQuestion,
    records: tuple[str, ...],
    ttl: int,
    now: int,
) -> None:
    """A network answer becomes a cache entry stamped with the time it arrived."""
    cache.entries[question_key(question)] = CacheEntry(
        records=records,
        stored_at=now,
        ttl=ttl,
    )
