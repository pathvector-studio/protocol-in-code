from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .chain import ChainOutcome, ChainResult, ZoneData, validate_chain
from .dnskey import DnsKey, KeyRole, make_key, sign_key_rrset
from .ds import Ds, make_ds
from .rrsig import Rrset, Rrsig, sign_rrset

DEFAULT_INCEPTION = 0
DEFAULT_EXPIRATION = 1_000_000


class AnswerMismatch(str, Enum):
    """The "answer" a resolver is handed must actually be an answer to the question it asked."""

    NAME_MISMATCH = "NameMismatch"
    TYPE_MISMATCH = "TypeMismatch"
    NONE = "None"


@dataclass(frozen=True)
class ValidationReport:
    outcome: ChainOutcome
    trace_slice: tuple[str, ...]


def format_trace(report: ValidationReport) -> str:
    """Render a report's trace as the multi-line log a doc author would paste under a demo."""
    return "\n".join(report.trace_slice)


@dataclass
class ToyValidatingResolver:
    """The toy validating resolver: given a signed answer, climb the zone tree to the trust anchor - or don't.

    A real validating resolver (RFC 4035 SS5) fetches DNSKEY, DS, and RRSIG
    records itself, hop by hop, over the network - the DNS track's
    walk_from_root and referral machinery already model that fan-out. This
    resolver is handed the whole tree up front (`zones`) plus a signed
    "answer" (an rrset and its covering rrsig) to check, so the interesting
    logic - the walk in chain.py - stays isolated from the transport concerns
    the DNS track already covers.

    By the end, the resolver ends up trusting exactly one key it was GIVEN
    (`trust_anchor`, pinned out of band) and every other fact - each ZSK,
    each KSK, each DS digest - it can ARITHMETIC its way up to by recomputing
    a sha256 and comparing. Nothing else is trusted on say-so.
    """

    zones: dict[str, ZoneData]
    trust_anchor: Ds
    clock: int = 0
    trace: list[str] = field(default_factory=list)

    def tick(self, seconds: int) -> None:
        self.clock += seconds

    def resolve_and_validate(self, name: str, rtype: str, rrset: Rrset, rrsig: Rrsig) -> ValidationReport:
        """Check that (name, rtype) matches the offered answer, then walk the chain to the trust anchor."""
        if rrset.name != name:
            self.trace.append(f"{name}: answer name mismatch ({rrset.name})")
            return ValidationReport(ChainOutcome.BOGUS_RECORD_SIG, (self.trace[-1],))
        if rrset.rtype != rtype:
            self.trace.append(f"{name}: answer type mismatch ({rrset.rtype} != {rtype})")
            return ValidationReport(ChainOutcome.BOGUS_RECORD_SIG, (self.trace[-1],))

        result: ChainResult = validate_chain(rrset, rrsig, self.zones, self.trust_anchor, self.clock)
        self.trace.extend(result.trace)
        return ValidationReport(outcome=result.outcome, trace_slice=result.trace)


def _make_zone(zone: str, secret_prefix: str) -> tuple[ZoneData, DnsKey]:
    """Build one zone's KSK/ZSK pair and its self-signed DNSKEY rrset. Returns the zone data and its KSK."""
    ksk = make_key(zone, KeyRole.KSK, f"{secret_prefix}-ksk-secret")
    zsk = make_key(zone, KeyRole.ZSK, f"{secret_prefix}-zsk-secret")
    keys = (ksk, zsk)
    key_rrsig = sign_key_rrset(keys, ksk, DEFAULT_INCEPTION, DEFAULT_EXPIRATION)
    zone_data = ZoneData(zone=zone, keys=keys, key_rrsig=key_rrsig, ds_for_children={})
    return zone_data, ksk


@dataclass(frozen=True)
class DemoTree:
    """A ready-to-validate root -> com -> example.com tree, plus the pieces needed to break each level.

    `tamper_record`, `tamper_ds`, and `unsign_child` each return a variant of
    this tree broken at one specific hop, so a doc author can show all four
    outcomes (SECURE and the three failure flavors) from the same starting
    point.
    """

    zones: dict[str, ZoneData]
    trust_anchor: Ds
    rrset: Rrset
    rrsig: Rrsig
    example_zsk: DnsKey


def build_demo_tree() -> DemoTree:
    """Three zones, correctly signed and delegated: root signs com's DS, com signs example.com's DS.

    The delegation chain mirrors the real tree: the root zone's DNSKEY rrset
    is the trust anchor's target, root holds a DS for com, and com holds a DS
    for example.com. example.com's ZSK signs the one demo answer, an A
    record for example.com itself.
    """
    root_data, root_ksk = _make_zone("", "root")
    com_data, com_ksk = _make_zone("com", "com")
    example_data, example_ksk = _make_zone("example.com", "example")

    root_data.ds_for_children["com"] = make_ds(com_ksk)
    com_data.ds_for_children["example.com"] = make_ds(example_ksk)

    zones = {"": root_data, "com": com_data, "example.com": example_data}
    trust_anchor = make_ds(root_ksk)

    example_zsk = next(key for key in example_data.keys if key.role is KeyRole.ZSK)
    rrset = Rrset(name="example.com", rtype="A", records=("192.0.2.10",))
    rrsig = sign_rrset(
        rrset, example_zsk.key_secret, example_zsk.key_tag, "example.com", DEFAULT_INCEPTION, DEFAULT_EXPIRATION
    )

    return DemoTree(zones=zones, trust_anchor=trust_anchor, rrset=rrset, rrsig=rrsig, example_zsk=example_zsk)


def tamper_record(tree: DemoTree) -> Rrset:
    """Swap the answer after it was signed, without re-signing it. Feed this rrset with the original rrsig.

    The signature covers the original records, so it no longer matches -
    yields BOGUS_RECORD_SIG at the very first hop.
    """
    return Rrset(name=tree.rrset.name, rtype=tree.rrset.rtype, records=("198.51.100.99",))


def tamper_ds(tree: DemoTree) -> DemoTree:
    """Replace com's DS for example.com with a digest of the wrong key. Yields BOGUS_DS_MISMATCH.

    Everything below the tamper (the record sig, the key sig) still checks
    out - only the cross-zone fingerprint fails, which is exactly the failure
    DS records exist to catch: a parent vouching for the wrong child key.
    """
    decoy = make_key("example.com", KeyRole.KSK, "not-the-real-ksk-secret")
    com_data = tree.zones["com"]
    tampered_com = ZoneData(
        zone=com_data.zone,
        keys=com_data.keys,
        key_rrsig=com_data.key_rrsig,
        ds_for_children={**com_data.ds_for_children, "example.com": make_ds(decoy)},
    )
    zones = {**tree.zones, "com": tampered_com}
    return DemoTree(zones=zones, trust_anchor=tree.trust_anchor, rrset=tree.rrset, rrsig=tree.rrsig, example_zsk=tree.example_zsk)


def unsign_child(tree: DemoTree) -> DemoTree:
    """Drop com's DS entry for example.com entirely - an unsigned delegation. Yields INSECURE, not BOGUS.

    Nothing is wrong here in the sense of a failed check: com simply never
    published a fingerprint for example.com, so there is nothing to compare
    against. A real resolver would confirm that absence with an NSEC/NSEC3
    proof over com's namespace before calling it INSECURE rather than
    treating a missing answer as a network hiccup; this toy just models the
    absence directly as a missing dict entry.
    """
    com_data = tree.zones["com"]
    ds_for_children = dict(com_data.ds_for_children)
    del ds_for_children["example.com"]
    unsigned_com = ZoneData(
        zone=com_data.zone, keys=com_data.keys, key_rrsig=com_data.key_rrsig, ds_for_children=ds_for_children
    )
    zones = {**tree.zones, "com": unsigned_com}
    return DemoTree(zones=zones, trust_anchor=tree.trust_anchor, rrset=tree.rrset, rrsig=tree.rrsig, example_zsk=tree.example_zsk)
