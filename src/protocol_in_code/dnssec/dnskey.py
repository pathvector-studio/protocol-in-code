from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum

from .rrsig import Rrset, Rrsig, sign_rrset

# Toy stand-in only: real DNSKEY records carry an algorithm id and public key
# material (RFC 4034 SS2.1), and the key tag is a checksum over that wire
# encoding (RFC 4034 Appendix B). Here key_tag is a sha256 of the secret
# reduced mod 65536 - deterministic and collision-shy enough for a toy, with
# no cryptographic strength claim.


class KeyRole(str, Enum):
    KSK = "Key Signing Key"
    ZSK = "Zone Signing Key"


@dataclass(frozen=True)
class DnsKey:
    zone: str
    role: KeyRole
    key_secret: str
    key_tag: int


def derive_key_tag(key_secret: str) -> int:
    """Stand-in for RFC 4034's key tag checksum: a hash of the key material, folded into 16 bits."""
    digest = hashlib.sha256(key_secret.encode()).hexdigest()
    return int(digest, 16) % 65536


def make_key(zone: str, role: KeyRole, key_secret: str) -> DnsKey:
    return DnsKey(zone=zone, role=role, key_secret=key_secret, key_tag=derive_key_tag(key_secret))


def key_rrset(zone: str, keys: tuple[DnsKey, ...]) -> Rrset:
    """The KSK and ZSK are published together as one DNSKEY rrset - each is data the other can point at."""
    records = tuple(f"{key.role.value}:{key.key_tag}" for key in keys)
    return Rrset(name=zone, rtype="DNSKEY", records=records)


def sign_key_rrset(
    keys: tuple[DnsKey, ...],
    ksk: DnsKey,
    inception: int,
    expiration: int,
) -> Rrsig:
    """The key signs the key: the KSK signs the DNSKEY rrset that contains both itself and the ZSK.

    Ordinary rrsets (A, MX, ...) are signed by the ZSK instead. Splitting the
    role in two lets the ZSK rotate on its own schedule - a new ZSK just needs
    a fresh KSK signature over the DNSKEY rrset, not a new fact in the parent
    zone. The KSK changes rarely, because rolling it means updating the DS
    record one level up (see ds.py).
    """
    rrset = key_rrset(ksk.zone, keys)
    return sign_rrset(rrset, ksk.key_secret, ksk.key_tag, ksk.zone, inception, expiration)
