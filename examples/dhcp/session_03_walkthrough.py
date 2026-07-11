from protocol_in_code.dhcp.offer import OFFER_HOLD_SECONDS
from protocol_in_code.dhcp.pool import (
    CANDIDATE_END,
    CANDIDATE_START,
    AddressPool,
    allocate,
    hold,
    next_free,
    release,
)


def main() -> None:
    print("Session 03 walkthrough: The pool hands out what's free")
    print()

    pool = AddressPool(network_prefix="192.0.2")

    first = next_free(pool, now=0)
    marker = "OK" if first == f"192.0.2.{CANDIDATE_START}" else "NG"
    print(f"[{marker}] first next_free gives .10               -> {first}")

    hold(pool, first, now=0)
    second = next_free(pool, now=0)
    marker = "OK" if second == f"192.0.2.{CANDIDATE_START + 1}" else "NG"
    print(f"[{marker}] holding .10 makes next_free skip to .11  -> {second}")

    still_held = next_free(pool, now=OFFER_HOLD_SECONDS - 1)
    marker = "OK" if still_held == f"192.0.2.{CANDIDATE_START + 1}" else "NG"
    print(f"[{marker}] just before hold expiry still skips .10  -> {still_held}")

    after_hold_expires = next_free(pool, now=OFFER_HOLD_SECONDS)
    marker = "OK" if after_hold_expires == f"192.0.2.{CANDIDATE_START}" else "NG"
    print(f"[{marker}] expired hold frees .10 again              -> {after_hold_expires}")

    allocate(pool, first)
    after_allocate = next_free(pool, now=OFFER_HOLD_SECONDS)
    marker = "OK" if after_allocate == f"192.0.2.{CANDIDATE_START + 1}" else "NG"
    print(f"[{marker}] allocate removes .10 permanently          -> {after_allocate}")

    release(pool, first)
    after_release = next_free(pool, now=OFFER_HOLD_SECONDS)
    marker = "OK" if after_release == f"192.0.2.{CANDIDATE_START}" else "NG"
    print(f"[{marker}] release returns .10 to the free pool      -> {after_release}")

    for host in range(CANDIDATE_START, CANDIDATE_END + 1):
        allocate(pool, f"192.0.2.{host}")
    exhausted = next_free(pool, now=OFFER_HOLD_SECONDS)
    marker = "OK" if exhausted is None else "NG"
    print(f"[{marker}] filling the whole range exhausts the pool -> {exhausted}")


if __name__ == "__main__":
    main()
