from protocol_in_code.tls.alert import AlertDescription
from protocol_in_code.tls.chain import Certificate
from protocol_in_code.tls.handshake_loop import (
    ToyTlsClient,
    ToyTlsConfig,
    ToyTlsServer,
    run_handshake,
    run_resumed_handshake,
)
from protocol_in_code.tls.resumption import TicketStore


def main() -> None:
    print("Session 09 walkthrough: Build the toy handshake loop")
    print()

    trust_store = {"Example Root CA": "root-key-id"}
    good_chain = (
        Certificate(
            subject="example.com",
            issuer="Example Root CA",
            public_key_id="leaf-key-id",
            not_before=0,
            not_after=1000,
            is_ca=False,
        ),
    )

    # Scenario 1: a full handshake that completes cleanly.
    client = ToyTlsClient(
        name="client",
        config=ToyTlsConfig(
            versions=("TLS1.3",),
            cipher_suites=("TLS_AES_128_GCM_SHA256",),
            chain=good_chain,
        ),
    )
    server = ToyTlsServer(
        name="server",
        config=ToyTlsConfig(
            versions=("TLS1.3",),
            cipher_suites=("TLS_AES_128_GCM_SHA256",),
            chain=good_chain,
            trust_store=trust_store,
        ),
        tickets=TicketStore(),
    )
    outcome = run_handshake(client, server, trust_store, now=0)
    marker = "OK" if outcome.completed and outcome.ticket_name is not None else "NG"
    print(f"[{marker}] full handshake completes            -> completed={outcome.completed} ticket={outcome.ticket_name}")

    marker = "OK" if len(client.trace) > 0 and len(server.trace) > 0 else "NG"
    print(f"[{marker}] both traces populated                -> client={len(client.trace)} lines, server={len(server.trace)} lines")

    # Scenario 2: no cipher suite overlap fails the handshake.
    no_overlap_client = ToyTlsClient(
        name="client",
        config=ToyTlsConfig(versions=("TLS1.3",), cipher_suites=("TLS_AES_128_GCM_SHA256",), chain=good_chain),
    )
    no_overlap_server = ToyTlsServer(
        name="server",
        config=ToyTlsConfig(
            versions=("TLS1.3",),
            cipher_suites=("TLS_CHACHA20_POLY1305_SHA256",),
            chain=good_chain,
            trust_store=trust_store,
        ),
    )
    no_overlap_outcome = run_handshake(no_overlap_client, no_overlap_server, trust_store, now=0)
    marker = (
        "OK"
        if not no_overlap_outcome.completed
        and no_overlap_outcome.alert is not None
        and no_overlap_outcome.alert.description is AlertDescription.HANDSHAKE_FAILURE
        else "NG"
    )
    print(f"[{marker}] no suite overlap -> HANDSHAKE_FAILURE  -> completed={no_overlap_outcome.completed} alert={no_overlap_outcome.alert}")

    # Scenario 3: an expired certificate fails the handshake.
    expired_chain = (
        Certificate(
            subject="example.com",
            issuer="Example Root CA",
            public_key_id="leaf-key-id",
            not_before=0,
            not_after=100,
            is_ca=False,
        ),
    )
    expired_client = ToyTlsClient(
        name="client",
        config=ToyTlsConfig(versions=("TLS1.3",), cipher_suites=("TLS_AES_128_GCM_SHA256",), chain=expired_chain),
    )
    expired_server = ToyTlsServer(
        name="server",
        config=ToyTlsConfig(
            versions=("TLS1.3",),
            cipher_suites=("TLS_AES_128_GCM_SHA256",),
            chain=expired_chain,
            trust_store=trust_store,
        ),
    )
    expired_outcome = run_handshake(expired_client, expired_server, trust_store, now=500)
    marker = (
        "OK"
        if not expired_outcome.completed
        and expired_outcome.alert is not None
        and expired_outcome.alert.description is AlertDescription.CERTIFICATE_EXPIRED
        else "NG"
    )
    print(f"[{marker}] expired cert -> CERTIFICATE_EXPIRED    -> completed={expired_outcome.completed} alert={expired_outcome.alert}")

    # Scenario 4: resumption using the ticket issued by scenario 1's full handshake.
    lines_before_resume = len(client.trace) + len(server.trace)
    resumed_outcome = run_resumed_handshake(client, server, outcome.ticket_name, now=1)
    marker = "OK" if resumed_outcome.completed else "NG"
    print(f"[{marker}] resumed handshake completes           -> completed={resumed_outcome.completed}")

    resumed_only_trace = resumed_outcome.trace[lines_before_resume:]
    has_skipped_line = any("SKIPPED" in line for line in resumed_only_trace)
    marker = "OK" if has_skipped_line else "NG"
    print(f"[{marker}] resumed trace contains a SKIPPED line -> {has_skipped_line}")

    # Scenario 5: the resumed path never re-verifies the chain.
    no_chain_verify = not any("verifies chain" in line for line in resumed_only_trace)
    marker = "OK" if no_chain_verify else "NG"
    print(f"[{marker}] resumed trace has no 'verifies chain' -> {no_chain_verify}")


if __name__ == "__main__":
    main()
