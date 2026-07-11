"""DNSSEC reading examples for the Protocol in Code course."""

from .chain import ChainOutcome, ChainResult, ZoneData, validate_chain
from .dnskey import DnsKey, KeyRole, derive_key_tag, key_rrset, make_key
from .dnskey import sign_key_rrset as sign_dnskey_rrset
from .ds import Ds, ds_digest, ds_matches, make_ds
from .rrsig import Rrset, Rrsig, VerifyOutcome, sign_rrset, verify_rrsig
from .validator_loop import (
    AnswerMismatch,
    DemoTree,
    ToyValidatingResolver,
    ValidationReport,
    build_demo_tree,
    format_trace,
    tamper_ds,
    tamper_record,
    unsign_child,
)

__all__ = [
    "AnswerMismatch",
    "ChainOutcome",
    "ChainResult",
    "DemoTree",
    "DnsKey",
    "Ds",
    "KeyRole",
    "Rrset",
    "Rrsig",
    "ToyValidatingResolver",
    "ValidationReport",
    "VerifyOutcome",
    "ZoneData",
    "build_demo_tree",
    "derive_key_tag",
    "ds_digest",
    "ds_matches",
    "format_trace",
    "key_rrset",
    "make_ds",
    "make_key",
    "sign_dnskey_rrset",
    "sign_rrset",
    "tamper_ds",
    "tamper_record",
    "unsign_child",
    "validate_chain",
    "verify_rrsig",
]
