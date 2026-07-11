from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# Same shape as src/protocol_in_code/dns/cache.py: a name maps to an entry with an
# issue time and a lifetime, and expiry is checked (and cleaned up) at lookup time.
# Different protocol, same lesson - caches and tickets are the same idea twice.


class TicketOutcome(str, Enum):
    HIT = "Hit"
    MISS = "Miss"
    EXPIRED = "Expired"


@dataclass(frozen=True)
class SessionTicket:
    master_secret: str
    cipher_suite: str
    issued_at: int
    lifetime: int


@dataclass
class TicketStore:
    tickets: dict[str, SessionTicket] = field(default_factory=dict)


@dataclass(frozen=True)
class TicketLookup:
    outcome: TicketOutcome
    ticket: SessionTicket | None


def ticket_is_expired(ticket: SessionTicket, now: int) -> bool:
    return now >= ticket.issued_at + ticket.lifetime


def lookup_ticket(store: TicketStore, name: str, now: int) -> TicketLookup:
    """Resumption is a cache hit: a valid ticket skips the expensive parts of the handshake."""
    ticket = store.tickets.get(name)
    if ticket is None:
        return TicketLookup(TicketOutcome.MISS, None)

    if ticket_is_expired(ticket, now):
        del store.tickets[name]
        return TicketLookup(TicketOutcome.EXPIRED, None)

    return TicketLookup(TicketOutcome.HIT, ticket)


def issue_ticket(
    store: TicketStore,
    name: str,
    master_secret: str,
    cipher_suite: str,
    lifetime: int,
    now: int,
) -> SessionTicket:
    """A completed handshake earns the client a fast path back in, stamped with the time it was issued."""
    ticket = SessionTicket(
        master_secret=master_secret,
        cipher_suite=cipher_suite,
        issued_at=now,
        lifetime=lifetime,
    )
    store.tickets[name] = ticket
    return ticket
