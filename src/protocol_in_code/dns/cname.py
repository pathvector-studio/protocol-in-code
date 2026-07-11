from __future__ import annotations

from dataclasses import dataclass

from .query import normalize_name

MAX_CHAIN_LENGTH = 8


@dataclass(frozen=True)
class ChainResult:
    resolved: bool
    final_name: str
    records: tuple[str, ...]
    chain: tuple[str, ...]
    stopped_because: str


def follow_cname(
    qname: str,
    qtype: str,
    records_by_name: dict[tuple[str, str], tuple[str, ...]],
    max_chain: int = MAX_CHAIN_LENGTH,
) -> ChainResult:
    """A CNAME does not answer the question. It replaces the name and asks again."""
    current = normalize_name(qname)
    chain: list[str] = [current]
    seen: set[str] = {current}

    for _ in range(max_chain):
        records = records_by_name.get((current, qtype))
        if records:
            return ChainResult(True, current, records, tuple(chain), "answer")

        cname_targets = records_by_name.get((current, "CNAME"))
        if not cname_targets:
            return ChainResult(False, current, (), tuple(chain), "no answer and no CNAME")

        target = normalize_name(cname_targets[0])
        if target in seen:
            return ChainResult(False, current, (), tuple(chain), "CNAME loop detected")

        current = target
        seen.add(current)
        chain.append(current)

    return ChainResult(False, current, (), tuple(chain), "chain length limit reached")
