from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .dnskey import DnsKey, KeyRole, key_rrset
from .ds import Ds, ds_matches
from .rrsig import Rrset, Rrsig, VerifyOutcome, verify_rrsig

# Cross-reference: see tls/chain.py for the sibling trust walk. Both walk from
# a leaf fact up to something already trusted, hop by hop. But the shapes
# differ. TLS's chain is a list of certificates that can end at ANY root
# sitting in a local trust store - many valid roots, chosen by whichever
# issuer signed the leaf. DNSSEC's chain is zone-cut hops within ONE tree
# (child -> parent -> grandparent -> ... -> root), and there is exactly one
# anchor: the root's key, trusted out of band and pinned once as
# `trust_anchor`. There is nowhere else the walk can end up.


class ChainOutcome(str, Enum):
    SECURE = "Secure"
    BOGUS_RECORD_SIG = "BogusRecordSignature"
    BOGUS_KEY_SIG = "BogusKeySignature"
    BOGUS_DS_MISMATCH = "BogusDsMismatch"
    INSECURE = "Insecure"


@dataclass(frozen=True)
class ZoneData:
    zone: str
    keys: tuple[DnsKey, ...]
    key_rrsig: Rrsig
    ds_for_children: dict[str, Ds]


@dataclass(frozen=True)
class ChainResult:
    outcome: ChainOutcome
    trace: tuple[str, ...]


def _find_key(keys: tuple[DnsKey, ...], role: KeyRole) -> DnsKey | None:
    for key in keys:
        if key.role is role:
            return key
    return None


def _zone_chain(zone: str) -> list[str]:
    """example.com -> ['example.com', 'com', '']  (the root zone is the empty string)."""
    labels = zone.split(".") if zone else []
    chain = []
    while True:
        chain.append(".".join(labels))
        if not labels:
            break
        labels = labels[1:]
    return chain


def validate_chain(
    rrset: Rrset,
    rrsig: Rrsig,
    zones: dict[str, ZoneData],
    trust_anchor: Ds,
    now: int,
) -> ChainResult:
    """Validation walks up the tree: record -> zone's ZSK -> zone's KSK -> parent's DS -> ... -> the trust anchor.

    Each hop rests on the one below it: the record's RRSIG must verify under
    the zone's ZSK, that ZSK must be part of a DNSKEY rrset the zone's own KSK
    signed, and that KSK must hash to the DS record the PARENT publishes for
    it. Climbing repeats this until a zone's KSK hashes to `trust_anchor`
    itself - the one key handed to the resolver out of band, arithmetic
    covering everything beneath it.

    A parent that has no DS entry for a child is INSECURE, not BOGUS: an
    unsigned delegation is a proven absence, not a broken proof. Here that
    absence is modeled by `ds_for_children` simply lacking the child's zone
    as a key. Real DNSSEC proves the absence itself with an NSEC/NSEC3
    record over the parent's namespace (RFC 4035 SS5.4); that proof is out of
    scope for this toy.
    """
    trace: list[str] = []
    owner = rrset.name

    zone_data = zones.get(owner)
    if zone_data is None:
        trace.append(f"{owner}: no zone data available")
        return ChainResult(ChainOutcome.INSECURE, tuple(trace))

    zsk = _find_key(zone_data.keys, KeyRole.ZSK)
    if zsk is None:
        trace.append(f"{owner}: no ZSK on file")
        return ChainResult(ChainOutcome.INSECURE, tuple(trace))

    record_outcome = verify_rrsig(rrset, rrsig, zsk.key_secret, now)
    if record_outcome is not VerifyOutcome.OK:
        trace.append(f"{owner}: record sig {record_outcome.value} (ZSK {zsk.key_tag})")
        return ChainResult(ChainOutcome.BOGUS_RECORD_SIG, tuple(trace))
    trace.append(f"{owner}: record sig OK (ZSK {zsk.key_tag})")

    for zone_name in _zone_chain(owner):
        current = zones.get(zone_name)
        if current is None:
            trace.append(f"{zone_name}: no zone data available")
            return ChainResult(ChainOutcome.INSECURE, tuple(trace))

        ksk = _find_key(current.keys, KeyRole.KSK)
        if ksk is None:
            trace.append(f"{zone_name}: no KSK on file")
            return ChainResult(ChainOutcome.INSECURE, tuple(trace))

        rrset_for_keys = key_rrset(zone_name, current.keys)
        key_sig_outcome = verify_rrsig(rrset_for_keys, current.key_rrsig, ksk.key_secret, now)
        if key_sig_outcome is not VerifyOutcome.OK:
            trace.append(f"{zone_name}: key sig {key_sig_outcome.value} (KSK {ksk.key_tag})")
            return ChainResult(ChainOutcome.BOGUS_KEY_SIG, tuple(trace))
        trace.append(f"{zone_name}: key sig OK (KSK {ksk.key_tag})")

        if zone_name == "":
            if not ds_matches(trust_anchor, ksk):
                trace.append(f"{zone_name}: KSK does not match trust anchor")
                return ChainResult(ChainOutcome.BOGUS_DS_MISMATCH, tuple(trace))
            trace.append(f"{zone_name}: KSK matches trust anchor")
            return ChainResult(ChainOutcome.SECURE, tuple(trace))

        parent_labels = zone_name.split(".")[1:]
        parent_name = ".".join(parent_labels)
        parent = zones.get(parent_name)
        if parent is None:
            trace.append(f"{parent_name}: no zone data available")
            return ChainResult(ChainOutcome.INSECURE, tuple(trace))

        ds = parent.ds_for_children.get(zone_name)
        if ds is None:
            trace.append(f"{parent_name}: no DS on file for {zone_name}")
            return ChainResult(ChainOutcome.INSECURE, tuple(trace))

        if not ds_matches(ds, ksk):
            trace.append(f"{parent_name}: DS for {zone_name} does not match KSK {ksk.key_tag}")
            return ChainResult(ChainOutcome.BOGUS_DS_MISMATCH, tuple(trace))
        trace.append(f"{parent_name}: KSK matches DS for {zone_name}")

    # Unreachable: the loop above always terminates at zone_name == "" (the root),
    # which returns directly.
    trace.append("chain walk fell off the tree")
    return ChainResult(ChainOutcome.INSECURE, tuple(trace))
