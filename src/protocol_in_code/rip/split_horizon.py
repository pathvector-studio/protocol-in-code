"""Don't tell me what I told you.

count_to_infinity.py shows the disease: a router advertises a route back to
the very neighbor that taught it that route, and the two of them count each
other up to infinity. The cure lives here, and it is not smarter math — it
is an outbound filter applied before a router speaks. Split horizon omits
any route whose next_hop is the neighbor being advertised to. Poisoned
reverse keeps the same route visible but announces it as unreachable, which
is louder and converges faster because the neighbor doesn't have to wait
for a timeout to notice the route is gone.
"""

from __future__ import annotations

from .infinity import INFINITY
from .update import RoutingTable


def advertisable(table: RoutingTable, to_neighbor: str) -> tuple[tuple[str, int], ...]:
    """Plain split horizon: silently drop routes learned from the neighbor we're telling."""
    advertised: list[tuple[str, int]] = []
    for prefix, route in sorted(table.routes.items()):
        if route.next_hop == to_neighbor:
            continue
        advertised.append((prefix, route.metric))
    return tuple(advertised)


def advertisable_with_poison(table: RoutingTable, to_neighbor: str) -> tuple[tuple[str, int], ...]:
    """Poisoned reverse: same routes, but the ones learned from this neighbor are sent
    back at INFINITY instead of being omitted — say it louder, don't just go quiet.
    """
    advertised: list[tuple[str, int]] = []
    for prefix, route in sorted(table.routes.items()):
        if route.next_hop == to_neighbor:
            advertised.append((prefix, INFINITY))
        else:
            advertised.append((prefix, route.metric))
    return tuple(advertised)
