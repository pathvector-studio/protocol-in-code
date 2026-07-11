from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Storage and reuse rules loosely follow RFC 9111 (HTTP Caching), sections 3 and 4.


class StoreDecision(str, Enum):
    STORE = "Store"
    DO_NOT_STORE = "DoNotStore"


class ReuseDecision(str, Enum):
    FRESH = "Fresh"
    STALE_MUST_REVALIDATE = "StaleMustRevalidate"
    MUST_FETCH = "MustFetch"


class RevalidationResult(str, Enum):
    NOT_MODIFIED_304 = "NotModified304"
    CHANGED_200 = "Changed200"


@dataclass(frozen=True)
class ResponseDirectives:
    no_store: bool = False
    no_cache: bool = False
    max_age: int | None = None
    etag: str | None = None


@dataclass(frozen=True)
class CachedResponse:
    stored_at: int
    max_age: int
    etag: str | None
    no_store: bool
    no_cache: bool


def can_store(response_directives: ResponseDirectives) -> StoreDecision:
    """Cacheable is a decision tree: RFC 9111 3, no-store wins over everything else."""
    if response_directives.no_store:
        return StoreDecision.DO_NOT_STORE

    if response_directives.max_age is None and response_directives.etag is None:
        # Nothing that would ever let us decide freshness or revalidate later.
        return StoreDecision.DO_NOT_STORE

    return StoreDecision.STORE


def can_reuse(entry: CachedResponse, now: int) -> ReuseDecision:
    """Cacheable is a decision tree: RFC 9111 4, no-cache and age are checked in order."""
    if entry.no_cache:
        # no-cache still permits storage, but every reuse must be revalidated first.
        return ReuseDecision.STALE_MUST_REVALIDATE

    age = now - entry.stored_at
    if age < entry.max_age:
        return ReuseDecision.FRESH

    if entry.etag is not None:
        return ReuseDecision.STALE_MUST_REVALIDATE

    return ReuseDecision.MUST_FETCH


def revalidate(entry: CachedResponse, current_etag: str) -> RevalidationResult:
    """A conditional request settles a stale entry: same tag means the body never changed."""
    if entry.etag is not None and entry.etag == current_etag:
        return RevalidationResult.NOT_MODIFIED_304
    return RevalidationResult.CHANGED_200


if __name__ == "__main__":
    # no-store beats max-age: even a directive offering a fresh lifetime is overridden.
    no_store_wins = ResponseDirectives(no_store=True, max_age=3600)
    assert can_store(no_store_wins) == StoreDecision.DO_NOT_STORE

    storable = ResponseDirectives(max_age=60)
    assert can_store(storable) == StoreDecision.STORE

    unstorable = ResponseDirectives()
    assert can_store(unstorable) == StoreDecision.DO_NOT_STORE

    fresh_entry = CachedResponse(stored_at=0, max_age=60, etag="v1", no_store=False, no_cache=False)
    assert can_reuse(fresh_entry, now=30) == ReuseDecision.FRESH
    assert can_reuse(fresh_entry, now=60) == ReuseDecision.STALE_MUST_REVALIDATE

    no_etag_entry = CachedResponse(stored_at=0, max_age=60, etag=None, no_store=False, no_cache=False)
    assert can_reuse(no_etag_entry, now=60) == ReuseDecision.MUST_FETCH

    no_cache_entry = CachedResponse(stored_at=0, max_age=60, etag="v1", no_store=False, no_cache=True)
    assert can_reuse(no_cache_entry, now=0) == ReuseDecision.STALE_MUST_REVALIDATE

    assert revalidate(fresh_entry, "v1") == RevalidationResult.NOT_MODIFIED_304
    assert revalidate(fresh_entry, "v2") == RevalidationResult.CHANGED_200

    print("[OK] caching.py")
