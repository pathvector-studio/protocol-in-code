from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ResponseKind(str, Enum):
    ANSWER = "Answer"
    REFERRAL = "Referral"
    NODATA = "NoData"
    NAME_ERROR = "NameError"
    SERVER_FAILURE = "ServerFailure"


@dataclass(frozen=True)
class ResourceRecord:
    name: str
    rtype: str
    value: str
    ttl: int = 300


@dataclass(frozen=True)
class ServerResponse:
    """What one server sent back, before the resolver decides what it means."""

    rcode: str = "NOERROR"
    answer_records: tuple[ResourceRecord, ...] = ()
    authority_ns: tuple[str, ...] = ()
    is_authoritative: bool = False


def classify_response(response: ServerResponse) -> ResponseKind:
    """Decide what a response means: only one of these branches drives the next step."""
    if response.rcode == "NXDOMAIN":
        return ResponseKind.NAME_ERROR
    if response.rcode != "NOERROR":
        return ResponseKind.SERVER_FAILURE

    if response.answer_records:
        return ResponseKind.ANSWER

    if response.authority_ns and not response.is_authoritative:
        return ResponseKind.REFERRAL

    return ResponseKind.NODATA


def referral_targets(response: ServerResponse) -> tuple[str, ...]:
    """The next servers to ask. Meaningful only when the response is a referral."""
    if classify_response(response) is not ResponseKind.REFERRAL:
        return ()
    return response.authority_ns
