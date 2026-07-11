from __future__ import annotations

from dataclasses import dataclass, field

from .alert import (
    Alert,
    alert_for_chain_verdict,
    alert_for_hostname_verdict,
    alert_for_negotiation_outcome,
    alert_for_unprotect_outcome,
)
from .chain import Certificate, ChainVerdict, verify_chain
from .hostname import HostnameVerdict, match_hostname
from .key_schedule import KeySchedule, advance_to_handshake, advance_to_master, start_schedule
from .messages import ClientHello, ServerHello
from .negotiate import NegotiationOutcome, choose_suite, choose_version
from .record import UnprotectOutcome, protect, unprotect
from .resumption import TicketOutcome, TicketStore, issue_ticket, lookup_ticket

SHARED_KEY = "toy-ecdhe-shared-secret"  # stand-in for a real (EC)DHE exchange; see key_schedule.py
TICKET_LIFETIME = 3600


@dataclass
class ToyTlsConfig:
    versions: tuple[str, ...]
    cipher_suites: tuple[str, ...]
    chain: tuple[Certificate, ...] = ()
    trust_store: dict[str, str] = field(default_factory=dict)


@dataclass
class ToyTlsClient:
    name: str
    config: ToyTlsConfig
    trace: list[str] = field(default_factory=list)


@dataclass
class ToyTlsServer:
    name: str
    config: ToyTlsConfig
    tickets: TicketStore = field(default_factory=TicketStore)
    trace: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HandshakeOutcome:
    completed: bool
    alert: Alert | None
    trace: tuple[str, ...]
    ticket_name: str | None = None


def _fail(client: ToyTlsClient, server: ToyTlsServer, alert: Alert) -> HandshakeOutcome:
    line = f"handshake aborted: {alert.level.value} {alert.description.value}"
    client.trace.append(line)
    server.trace.append(line)
    return HandshakeOutcome(False, alert, tuple(client.trace + server.trace))


def run_handshake(
    client: ToyTlsClient,
    server: ToyTlsServer,
    trust_store: dict[str, str],
    now: int,
) -> HandshakeOutcome:
    """Build the toy handshake loop: hello, negotiate, verify, derive keys, ticket, protect one record."""
    hostname = client.config.chain[0].subject if client.config.chain else "example.com"
    hello = ClientHello(
        offered_versions=client.config.versions,
        cipher_suites=client.config.cipher_suites,
        server_name=hostname,
    )
    client.trace.append(f"client sends ClientHello: versions={hello.offered_versions} suites={hello.cipher_suites}")

    version_result = choose_version(hello.offered_versions, server.config.versions)
    if version_result.outcome is not NegotiationOutcome.CHOSEN:
        server.trace.append(f"negotiate version: {version_result.note}")
        return _fail(client, server, alert_for_negotiation_outcome(version_result.outcome))

    suite_result = choose_suite(hello.cipher_suites, server.config.cipher_suites)
    server.trace.append(f"negotiate suite: {suite_result.note}")
    if suite_result.outcome is not NegotiationOutcome.CHOSEN:
        return _fail(client, server, alert_for_negotiation_outcome(suite_result.outcome))

    server_hello = ServerHello(chosen_version=version_result.chosen, chosen_suite=suite_result.chosen)
    server.trace.append(f"server sends ServerHello: version={server_hello.chosen_version} suite={server_hello.chosen_suite}")

    server.trace.append(f"server presents chain of {len(server.config.chain)} certificate(s)")
    chain_verdict = verify_chain(server.config.chain, trust_store, now)
    client.trace.append(f"client verifies chain: {chain_verdict.value}")
    if chain_verdict is not ChainVerdict.TRUSTED:
        return _fail(client, server, alert_for_chain_verdict(chain_verdict))

    leaf = server.config.chain[0]
    san_names = (leaf.subject,)
    hostname_match = match_hostname(hostname, san_names)
    client.trace.append(f"client verifies hostname: {hostname_match.verdict.value}")
    if hostname_match.verdict is HostnameVerdict.NO_MATCH:
        return _fail(client, server, alert_for_hostname_verdict(hostname_match.verdict))

    client_schedule = start_schedule()
    server_schedule = start_schedule()
    advance_to_handshake(client_schedule, SHARED_KEY)
    advance_to_handshake(server_schedule, SHARED_KEY)
    advance_to_master(client_schedule)
    advance_to_master(server_schedule)
    client.trace.append("client advances key schedule: early -> handshake -> master")
    server.trace.append("server advances key schedule: early -> handshake -> master")

    ticket_name = f"ticket-for-{hostname}"
    issue_ticket(
        server.tickets,
        ticket_name,
        master_secret=server_schedule.master_secret,
        cipher_suite=server_hello.chosen_suite,
        lifetime=TICKET_LIFETIME,
        now=now,
    )
    server.trace.append(f"server issues session ticket: {ticket_name}")

    application_key = client_schedule.master_secret
    record = protect("application data", application_key, seq=0)
    client.trace.append(f"client protects one record: content_type={record.content_type} seq={record.seq}")
    unprotected = unprotect(record, application_key)
    server.trace.append(f"server unprotects record: {unprotected.outcome.value}")
    if unprotected.outcome is not UnprotectOutcome.OK:
        return _fail(client, server, alert_for_unprotect_outcome(unprotected.outcome))

    client.trace.append("handshake completed")
    server.trace.append("handshake completed")
    return HandshakeOutcome(True, None, tuple(client.trace + server.trace), ticket_name)


def run_resumed_handshake(
    client: ToyTlsClient,
    server: ToyTlsServer,
    ticket_name: str,
    now: int,
) -> HandshakeOutcome:
    """A ticket HIT resumes the session and skips chain verification entirely - the trace shows the skip."""
    client.trace.append(f"client offers session_ticket={ticket_name}")

    lookup = lookup_ticket(server.tickets, ticket_name, now)
    server.trace.append(f"server looks up ticket: {lookup.outcome.value}")

    if lookup.outcome is not TicketOutcome.HIT:
        server.trace.append("no valid ticket: falling back to a full handshake")
        return run_handshake(client, server, server.config.trust_store, now)

    server.trace.append("chain verification SKIPPED: resuming from ticket's master secret")
    client.trace.append("chain verification SKIPPED: resuming from ticket's master secret")

    resumed_schedule = start_schedule(psk=lookup.ticket.master_secret)
    advance_to_handshake(resumed_schedule, SHARED_KEY)
    advance_to_master(resumed_schedule)
    client.trace.append("client advances resumed key schedule: early -> handshake -> master")
    server.trace.append("server advances resumed key schedule: early -> handshake -> master")

    record = protect("application data", resumed_schedule.master_secret, seq=0)
    client.trace.append(f"client protects one record: content_type={record.content_type} seq={record.seq}")
    unprotected = unprotect(record, resumed_schedule.master_secret)
    server.trace.append(f"server unprotects record: {unprotected.outcome.value}")
    if unprotected.outcome is not UnprotectOutcome.OK:
        return _fail(client, server, alert_for_unprotect_outcome(unprotected.outcome))

    client.trace.append("resumed handshake completed")
    server.trace.append("resumed handshake completed")
    return HandshakeOutcome(True, None, tuple(client.trace + server.trace), ticket_name)
