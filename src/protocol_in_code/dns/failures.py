from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FailureKind(str, Enum):
    NAME_ERROR = "NXDOMAIN"
    SERVER_FAILURE = "SERVFAIL"
    REFUSED = "REFUSED"
    TIMEOUT = "Timeout"
    ANSWERED = "Answered"


@dataclass(frozen=True)
class ServerAttempt:
    """One try against one server: either a response with an rcode, or silence."""

    server: str
    timed_out: bool = False
    rcode: str = "NOERROR"
    records: tuple[str, ...] = ()


@dataclass(frozen=True)
class FallbackResult:
    kind: FailureKind
    records: tuple[str, ...]
    answered_by: str
    tried: tuple[str, ...]


def classify_attempt(attempt: ServerAttempt) -> FailureKind:
    if attempt.timed_out:
        return FailureKind.TIMEOUT
    if attempt.rcode == "NXDOMAIN":
        return FailureKind.NAME_ERROR
    if attempt.rcode == "SERVFAIL":
        return FailureKind.SERVER_FAILURE
    if attempt.rcode == "REFUSED":
        return FailureKind.REFUSED
    return FailureKind.ANSWERED


def is_final(kind: FailureKind) -> bool:
    """NXDOMAIN is an answer about the name. The rest are complaints about a server."""
    return kind in (FailureKind.ANSWERED, FailureKind.NAME_ERROR)


def try_servers(attempts: tuple[ServerAttempt, ...]) -> FallbackResult:
    """Walk the server list in order. Stop on a final outcome, move on for anything else."""
    tried: list[str] = []
    last_kind = FailureKind.SERVER_FAILURE

    for attempt in attempts:
        tried.append(attempt.server)
        kind = classify_attempt(attempt)

        if is_final(kind):
            return FallbackResult(kind, attempt.records, attempt.server, tuple(tried))

        last_kind = kind

    return FallbackResult(last_kind, (), "", tuple(tried))
