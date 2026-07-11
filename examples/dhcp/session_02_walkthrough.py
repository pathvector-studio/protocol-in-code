from protocol_in_code.dhcp.offer import (
    OFFER_HOLD_SECONDS,
    accept_offer,
    make_offer,
    offer_is_stale,
)


def main() -> None:
    print("Session 02 walkthrough: An offer is a proposal with a deadline")
    print()

    offer = make_offer(ip="192.0.2.10", lease_seconds=3600, server_id="192.0.2.1", now=0)

    marker = "OK" if not offer_is_stale(offer, now=0) else "NG"
    print(f"[{marker}] fresh offer at made_at is not stale        -> stale={offer_is_stale(offer, now=0)}")

    just_before = OFFER_HOLD_SECONDS - 1
    marker = "OK" if not offer_is_stale(offer, now=just_before) else "NG"
    print(f"[{marker}] one second before the deadline is not stale -> stale={offer_is_stale(offer, now=just_before)}")

    at_deadline = offer.made_at + OFFER_HOLD_SECONDS
    marker = "OK" if offer_is_stale(offer, now=at_deadline) else "NG"
    print(f"[{marker}] at exactly made_at + {OFFER_HOLD_SECONDS} is stale     -> stale={offer_is_stale(offer, now=at_deadline)}")

    past_deadline = at_deadline + 1
    marker = "OK" if offer_is_stale(offer, now=past_deadline) else "NG"
    print(f"[{marker}] one second past the deadline is stale       -> stale={offer_is_stale(offer, now=past_deadline)}")

    request = accept_offer(offer, client_mac="aa:bb:cc:00:00:01", transaction_id=1)
    echoes_server = request.server_id == offer.server_id
    echoes_ip = request.requested_ip == offer.ip
    marker = "OK" if echoes_server and echoes_ip else "NG"
    print(
        f"[{marker}] REQUEST echoes server_id AND ip (losers self-release) "
        f"-> server_id={request.server_id} requested_ip={request.requested_ip}"
    )


if __name__ == "__main__":
    main()
