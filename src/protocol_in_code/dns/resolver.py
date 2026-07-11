from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .cache import CacheOutcome, ResolverCache, lookup, store
from .cname import MAX_CHAIN_LENGTH
from .query import DNSQuestion, QuestionValidity, normalize_name, validate_question
from .walk import Zone, walk_from_root

DEFAULT_TTL = 300


class ResolveSource(str, Enum):
    REJECTED = "Rejected"
    CACHE = "Cache"
    NETWORK = "Network"
    FAILED = "Failed"


@dataclass(frozen=True)
class ResolveResult:
    source: ResolveSource
    records: tuple[str, ...]
    trace: tuple[str, ...]


@dataclass
class ToyResolver:
    """The smallest readable resolver: validate, ask the cache, walk the tree, follow CNAME."""

    zones: dict[str, Zone]
    cache: ResolverCache = field(default_factory=ResolverCache)
    clock: int = 0
    default_ttl: int = DEFAULT_TTL

    def tick(self, seconds: int) -> None:
        self.clock += seconds

    def resolve(self, question: DNSQuestion) -> ResolveResult:
        trace: list[str] = []

        validity = validate_question(question)
        if validity is not QuestionValidity.VALID:
            trace.append(f"rejected: {validity.value}")
            return ResolveResult(ResolveSource.REJECTED, (), tuple(trace))

        cached = lookup(self.cache, question, self.clock)
        trace.append(f"cache: {cached.outcome.value}")
        if cached.outcome is CacheOutcome.HIT:
            return ResolveResult(ResolveSource.CACHE, cached.records, tuple(trace))

        current = DNSQuestion(
            qname=normalize_name(question.qname),
            qtype=question.qtype,
            qclass=question.qclass,
        )

        for _ in range(MAX_CHAIN_LENGTH):
            walked = walk_from_root(current, self.zones)
            trace.append(f"walk {current.qname}: {' -> '.join(walked.path)} ({walked.stopped_because})")

            if walked.found:
                store(self.cache, question, walked.records, self.default_ttl, self.clock)
                return ResolveResult(ResolveSource.NETWORK, walked.records, tuple(trace))

            cname_question = DNSQuestion(qname=current.qname, qtype="CNAME", qclass=current.qclass)
            cname_walk = walk_from_root(cname_question, self.zones)
            if not cname_walk.found:
                return ResolveResult(ResolveSource.FAILED, (), tuple(trace))

            target = normalize_name(cname_walk.records[0])
            trace.append(f"cname: {current.qname} -> {target}")
            current = DNSQuestion(qname=target, qtype=question.qtype, qclass=question.qclass)

        trace.append("cname chain limit reached")
        return ResolveResult(ResolveSource.FAILED, (), tuple(trace))
