from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum

# Toy stand-in only: real DNSSEC signs with RSA or ECDSA over a canonical wire
# encoding of the rrset (RFC 4034 SS3.1.8.1). Here a single sha256 hexdigest over
# (key_secret, name, rtype, sorted records, validity window) plays the role of
# that signature. No cryptographic strength claim is made - anyone who knows
# key_secret can forge one.
#
# The thesis: the signature is DATA in the zone, served right next to the
# answer it covers. Contrast TLS, where trust rides the pipe (the handshake
# authenticates a connection); DNSSEC signs the *contents* - the same signed
# answer is valid whether it arrives over UDP, TCP, or a cache that has never
# spoken to the authoritative server at all.


class VerifyOutcome(str, Enum):
    OK = "Ok"
    BAD_SIGNATURE = "BadSignature"
    EXPIRED = "Expired"
    NOT_YET_VALID = "NotYetValid"
    WRONG_NAME = "WrongName"


@dataclass(frozen=True)
class Rrset:
    name: str
    rtype: str
    records: tuple[str, ...]


@dataclass(frozen=True)
class Rrsig:
    covered_name: str
    covered_type: str
    signer: str
    key_tag: int
    signature: str
    inception: int
    expiration: int


def _signature_material(rrset: Rrset, key_secret: str, inception: int, expiration: int) -> bytes:
    sorted_records = "|".join(sorted(rrset.records))
    material = f"{key_secret}|{rrset.name}|{rrset.rtype}|{sorted_records}|{inception}|{expiration}"
    return material.encode()


def sign_rrset(
    rrset: Rrset,
    key_secret: str,
    key_tag: int,
    signer: str,
    inception: int,
    expiration: int,
) -> Rrsig:
    """A signature is produced once, over the rrset and the window it is valid for, then travels with it."""
    signature = hashlib.sha256(_signature_material(rrset, key_secret, inception, expiration)).hexdigest()
    return Rrsig(
        covered_name=rrset.name,
        covered_type=rrset.rtype,
        signer=signer,
        key_tag=key_tag,
        signature=signature,
        inception=inception,
        expiration=expiration,
    )


def verify_rrsig(rrset: Rrset, rrsig: Rrsig, key_secret: str, now: int) -> VerifyOutcome:
    """Recompute the toy signature and compare - the only inputs a verifier ever needs are the rrset and the key."""
    if rrset.name != rrsig.covered_name or rrset.rtype != rrsig.covered_type:
        return VerifyOutcome.WRONG_NAME

    if now < rrsig.inception:
        return VerifyOutcome.NOT_YET_VALID
    if now >= rrsig.expiration:
        return VerifyOutcome.EXPIRED

    expected = hashlib.sha256(
        _signature_material(rrset, key_secret, rrsig.inception, rrsig.expiration)
    ).hexdigest()
    if expected != rrsig.signature:
        return VerifyOutcome.BAD_SIGNATURE

    return VerifyOutcome.OK
