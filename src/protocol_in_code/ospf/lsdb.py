from __future__ import annotations

from dataclasses import dataclass, field

from .lsa import RouterLSA, is_newer_lsa, router_lsa_key


@dataclass
class LinkStateDatabase:
    areas: dict[str, dict[tuple[str, str], RouterLSA]] = field(default_factory=dict)

    def install_router_lsa(self, lsa: RouterLSA) -> bool:
        area_bucket = self.areas.setdefault(lsa.area_id, {})
        key = router_lsa_key(lsa)
        current = area_bucket.get(key)
        if current is not None and not is_newer_lsa(lsa, current):
            return False
        area_bucket[key] = lsa
        return True

    def router_lsas(self, area_id: str) -> tuple[RouterLSA, ...]:
        area_bucket = self.areas.get(area_id, {})
        return tuple(
            sorted(
                area_bucket.values(),
                key=lambda lsa: (lsa.header.advertising_router, lsa.header.lsa_id),
            )
        )

