from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ChainVerdict(str, Enum):
    TRUSTED = "Trusted"
    BROKEN_CHAIN = "BrokenChain"
    EXPIRED = "Expired"
    NOT_YET_VALID = "NotYetValid"
    UNTRUSTED_ROOT = "UntrustedRoot"
    EMPTY_CHAIN = "EmptyChain"


@dataclass(frozen=True)
class Certificate:
    subject: str
    issuer: str
    public_key_id: str
    not_before: int
    not_after: int
    is_ca: bool


def verify_chain(chain: tuple[Certificate, ...], trust_store: dict[str, str], now: int) -> ChainVerdict:
    """Trust is a walk up the chain: leaf to issuer to issuer, until a trusted root ends it."""
    if not chain:
        return ChainVerdict.EMPTY_CHAIN

    for cert in chain:
        if now < cert.not_before:
            return ChainVerdict.NOT_YET_VALID
        if now >= cert.not_after:
            return ChainVerdict.EXPIRED

    for position in range(len(chain) - 1):
        current = chain[position]
        next_cert = chain[position + 1]
        if current.issuer != next_cert.subject:
            return ChainVerdict.BROKEN_CHAIN

    last = chain[-1]
    if trust_store.get(last.issuer) is None:
        return ChainVerdict.UNTRUSTED_ROOT

    return ChainVerdict.TRUSTED
