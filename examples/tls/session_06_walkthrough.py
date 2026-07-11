from protocol_in_code.tls.resumption import TicketOutcome, TicketStore, issue_ticket, lookup_ticket


def main() -> None:
    print("Session 06 walkthrough: Resumption is a cache hit")
    print()

    store = TicketStore()
    name = "example.com"

    first = lookup_ticket(store, name, now=0)
    marker = "OK" if first.outcome is TicketOutcome.MISS else "NG"
    print(f"[{marker}] empty store                -> {first.outcome.value}")

    issue_ticket(store, name, master_secret="secret-abc123", cipher_suite="TLS_AES_128_GCM_SHA256", lifetime=300, now=0)

    second = lookup_ticket(store, name, now=10)
    marker = "OK" if second.outcome is TicketOutcome.HIT and second.ticket.master_secret == "secret-abc123" else "NG"
    print(f"[{marker}] after issue, 10s later     -> {second.outcome.value} {second.ticket.master_secret!r}")

    still_hit = lookup_ticket(store, name, now=299)
    marker = "OK" if still_hit.outcome is TicketOutcome.HIT else "NG"
    print(f"[{marker}] one tick before expiry     -> {still_hit.outcome.value}")

    expired = lookup_ticket(store, name, now=300)
    marker = "OK" if expired.outcome is TicketOutcome.EXPIRED else "NG"
    print(f"[{marker}] at exactly issued_at+lifetime -> {expired.outcome.value}")

    after_expiry = lookup_ticket(store, name, now=301)
    marker = "OK" if after_expiry.outcome is TicketOutcome.MISS else "NG"
    print(f"[{marker}] expired ticket was removed -> {after_expiry.outcome.value}")


if __name__ == "__main__":
    main()
