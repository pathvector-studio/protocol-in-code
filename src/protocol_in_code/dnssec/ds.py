from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .dnskey import DnsKey, KeyRole

# Toy stand-in only: a real DS digest is SHA-256 over the owner name and the
# wire-encoded DNSKEY RDATA (RFC 4509). Here it is a sha256 hexdigest over
# (zone, key_tag, key material) - same idea, no wire format, no cryptographic
# strength claim.


@dataclass(frozen=True)
class Ds:
    child_zone: str
    key_tag: int
    digest: str


def ds_digest(key: DnsKey) -> str:
    """Fingerprint a KSK down to a short, comparable digest."""
    material = f"{key.zone}|{key.key_tag}|{key.key_secret}".encode()
    return hashlib.sha256(material).hexdigest()


def make_ds(child_ksk: DnsKey) -> Ds:
    """The thesis: the parent zone stores a FINGERPRINT of the child's KSK.

    This is the one cross-zone fact that stitches the tree together - it is
    data in the PARENT, served alongside the delegation to the child. A
    resolver that already trusts the parent can trust the child's KSK the
    moment its DNSKEY rrset hashes to this DS record, with no separate
    out-of-band introduction needed.
    """
    if child_ksk.role is not KeyRole.KSK:
        raise ValueError("a DS record digests a KSK, not a ZSK")
    return Ds(child_zone=child_ksk.zone, key_tag=child_ksk.key_tag, digest=ds_digest(child_ksk))


def ds_matches(ds: Ds, key: DnsKey) -> bool:
    """Recompute the digest from the candidate key and compare - the whole of DS validation in one step."""
    return ds.child_zone == key.zone and ds.key_tag == key.key_tag and ds.digest == ds_digest(key)
