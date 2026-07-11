"""TLS reading examples for the Protocol in Code course."""

from .alert import (
    Alert,
    AlertAction,
    AlertDescription,
    AlertLevel,
    alert_for_chain_verdict,
    alert_for_hostname_verdict,
    alert_for_negotiation_outcome,
    alert_for_unprotect_outcome,
    classify,
)
from .chain import Certificate, ChainVerdict, verify_chain
from .handshake_loop import (
    SHARED_KEY,
    TICKET_LIFETIME,
    HandshakeOutcome,
    ToyTlsClient,
    ToyTlsConfig,
    ToyTlsServer,
    run_handshake,
    run_resumed_handshake,
)
from .hostname import HostnameMatch, HostnameVerdict, match_hostname, matches_exact, matches_wildcard
from .key_schedule import KeySchedule, advance_to_handshake, advance_to_master
from .key_schedule import derive as derive_key
from .key_schedule import start_schedule
from .messages import ClientHello, HelloValidity, ServerHello, validate_client_hello
from .negotiate import NegotiationOutcome, NegotiationResult, choose_alpn, choose_suite, choose_version
from .record import Record, UnprotectOutcome, UnprotectResult, protect, unprotect
from .resumption import SessionTicket, TicketLookup, TicketOutcome, TicketStore, issue_ticket, lookup_ticket
from .resumption import ticket_is_expired

__all__ = [
    "SHARED_KEY",
    "TICKET_LIFETIME",
    "Alert",
    "AlertAction",
    "AlertDescription",
    "AlertLevel",
    "Certificate",
    "ChainVerdict",
    "ClientHello",
    "HandshakeOutcome",
    "HelloValidity",
    "HostnameMatch",
    "HostnameVerdict",
    "KeySchedule",
    "NegotiationOutcome",
    "NegotiationResult",
    "Record",
    "ServerHello",
    "SessionTicket",
    "TicketLookup",
    "TicketOutcome",
    "TicketStore",
    "ToyTlsClient",
    "ToyTlsConfig",
    "ToyTlsServer",
    "UnprotectOutcome",
    "UnprotectResult",
    "advance_to_handshake",
    "advance_to_master",
    "alert_for_chain_verdict",
    "alert_for_hostname_verdict",
    "alert_for_negotiation_outcome",
    "alert_for_unprotect_outcome",
    "choose_alpn",
    "choose_suite",
    "choose_version",
    "classify",
    "derive_key",
    "issue_ticket",
    "lookup_ticket",
    "match_hostname",
    "matches_exact",
    "matches_wildcard",
    "protect",
    "run_handshake",
    "run_resumed_handshake",
    "start_schedule",
    "ticket_is_expired",
    "unprotect",
    "validate_client_hello",
]
