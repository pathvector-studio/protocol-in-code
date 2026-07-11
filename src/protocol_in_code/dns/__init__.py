"""DNS reading examples for the Protocol in Code course."""

from .cache import CacheEntry, CacheLookup, CacheOutcome, ResolverCache, entry_is_expired, lookup, store
from .cname import ChainResult, follow_cname
from .failures import FailureKind, FallbackResult, ServerAttempt, classify_attempt, is_final, try_servers
from .query import (
    DNSQuestion,
    QuestionValidity,
    normalize_name,
    question_key,
    validate_question,
)
from .referral import ResourceRecord, ResponseKind, ServerResponse, classify_response, referral_targets
from .resolver import ResolveResult, ResolveSource, ToyResolver
from .ttl import prune_expired, refresh_needed, remaining_ttl, served_ttl
from .walk import Zone, WalkResult, pick_delegation, walk_from_root, zone_covers

__all__ = [
    "CacheEntry",
    "CacheLookup",
    "CacheOutcome",
    "ChainResult",
    "DNSQuestion",
    "FailureKind",
    "FallbackResult",
    "QuestionValidity",
    "ResolveResult",
    "ResolveSource",
    "ResolverCache",
    "ResourceRecord",
    "ResponseKind",
    "ServerAttempt",
    "ServerResponse",
    "ToyResolver",
    "WalkResult",
    "Zone",
    "classify_attempt",
    "classify_response",
    "entry_is_expired",
    "follow_cname",
    "is_final",
    "lookup",
    "normalize_name",
    "pick_delegation",
    "prune_expired",
    "question_key",
    "referral_targets",
    "refresh_needed",
    "remaining_ttl",
    "served_ttl",
    "store",
    "try_servers",
    "validate_question",
    "walk_from_root",
    "zone_covers",
]
