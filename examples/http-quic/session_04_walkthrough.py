from protocol_in_code.http.caching import (
    CachedResponse,
    ResponseDirectives,
    ReuseDecision,
    RevalidationResult,
    StoreDecision,
    can_reuse,
    can_store,
    revalidate,
)


def main() -> None:
    print("Session 04 walkthrough: Cacheable is a decision tree")
    print()

    no_store_wins = ResponseDirectives(no_store=True, max_age=3600)
    decision = can_store(no_store_wins)
    marker = "OK" if decision is StoreDecision.DO_NOT_STORE else "NG"
    print(f"[{marker}] no-store beats max-age     -> {decision.value}")

    storable = ResponseDirectives(max_age=60)
    decision = can_store(storable)
    marker = "OK" if decision is StoreDecision.STORE else "NG"
    print(f"[{marker}] max-age alone is storable  -> {decision.value}")

    nothing_to_go_on = ResponseDirectives()
    decision = can_store(nothing_to_go_on)
    marker = "OK" if decision is StoreDecision.DO_NOT_STORE else "NG"
    print(f"[{marker}] no max-age and no etag     -> {decision.value}")

    entry = CachedResponse(stored_at=0, max_age=60, etag="v1", no_store=False, no_cache=False)
    reuse = can_reuse(entry, now=30)
    marker = "OK" if reuse is ReuseDecision.FRESH else "NG"
    print(f"[{marker}] within max_age             -> {reuse.value}")

    reuse = can_reuse(entry, now=60)
    marker = "OK" if reuse is ReuseDecision.STALE_MUST_REVALIDATE else "NG"
    print(f"[{marker}] past max_age, has etag     -> {reuse.value}")

    no_etag_entry = CachedResponse(stored_at=0, max_age=60, etag=None, no_store=False, no_cache=False)
    reuse = can_reuse(no_etag_entry, now=60)
    marker = "OK" if reuse is ReuseDecision.MUST_FETCH else "NG"
    print(f"[{marker}] past max_age, no etag      -> {reuse.value}")

    same_etag = revalidate(entry, "v1")
    marker = "OK" if same_etag is RevalidationResult.NOT_MODIFIED_304 else "NG"
    print(f"[{marker}] revalidate, matching etag  -> {same_etag.value}")

    changed_etag = revalidate(entry, "v2")
    marker = "OK" if changed_etag is RevalidationResult.CHANGED_200 else "NG"
    print(f"[{marker}] revalidate, changed etag   -> {changed_etag.value}")

    no_cache_entry = CachedResponse(stored_at=0, max_age=60, etag="v1", no_store=False, no_cache=True)
    reuse = can_reuse(no_cache_entry, now=0)
    marker = "OK" if reuse is ReuseDecision.STALE_MUST_REVALIDATE else "NG"
    print(f"[{marker}] no-cache forces revalidate -> {reuse.value} (even at age 0)")


if __name__ == "__main__":
    main()
