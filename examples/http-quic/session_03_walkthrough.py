from protocol_in_code.http.pool import IDLE_TIMEOUT, CheckoutOutcome, ConnectionPool, checkin, checkout


def main() -> None:
    print("Session 03 walkthrough: Keep-alive is a pool")
    print()

    pool = ConnectionPool()

    first = checkout(pool, "example.com", now=0)
    marker = "OK" if first.outcome is CheckoutOutcome.NEW else "NG"
    print(f"[{marker}] first checkout, empty pool -> {first.outcome.value} conn={first.conn_id}")

    checkin(pool, "example.com", first.conn_id, now=0)
    reused = checkout(pool, "example.com", now=10)
    marker = "OK" if (
        reused.outcome is CheckoutOutcome.REUSED and reused.conn_id == first.conn_id
    ) else "NG"
    print(f"[{marker}] checkin then checkout 10s  -> {reused.outcome.value} conn={reused.conn_id}")

    checkin(pool, "example.com", reused.conn_id, now=10)
    past_timeout = checkout(pool, "example.com", now=10 + IDLE_TIMEOUT + 1)
    marker = "OK" if past_timeout.outcome is CheckoutOutcome.NEW else "NG"
    print(f"[{marker}] idle past timeout          -> {past_timeout.outcome.value} conn={past_timeout.conn_id}")

    checkin(pool, "example.com", past_timeout.conn_id, now=41)
    at_boundary = checkout(pool, "example.com", now=41 + IDLE_TIMEOUT)
    marker = "OK" if at_boundary.outcome is CheckoutOutcome.NEW else "NG"
    print(f"[{marker}] at exactly IDLE_TIMEOUT    -> {at_boundary.outcome.value} conn={at_boundary.conn_id} (boundary)")

    checkin(pool, "example.com", at_boundary.conn_id, now=100)
    still_fresh = checkout(pool, "example.com", now=100 + IDLE_TIMEOUT - 1)
    marker = "OK" if (
        still_fresh.outcome is CheckoutOutcome.REUSED and still_fresh.conn_id == at_boundary.conn_id
    ) else "NG"
    print(f"[{marker}] one second inside timeout  -> {still_fresh.outcome.value} conn={still_fresh.conn_id}")

    checkin(pool, "example.com", still_fresh.conn_id, now=100 + IDLE_TIMEOUT - 1)
    other_host = checkout(pool, "other.example.com", now=100 + IDLE_TIMEOUT - 1)
    marker = "OK" if other_host.outcome is CheckoutOutcome.NEW else "NG"
    print(f"[{marker}] different host, same pool  -> {other_host.outcome.value} conn={other_host.conn_id}")


if __name__ == "__main__":
    main()
