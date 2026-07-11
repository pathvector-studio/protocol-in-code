"""Session thesis: covering is prefix math.

"Does this ROA say anything about this announcement?" is really two separate
questions, and conflating them is the classic operator mistake:

  1. Is the announced prefix inside the ROA's address range at all?
  2. If so, is the announcement specific enough to be within the ROA's
     max_length, or has it been sliced thinner than the holder authorized?

Both must hold before a ROA is relevant to an announcement. Keeping them as
two separate functions (rather than one bool-returning "matches") is
deliberate: it mirrors how a real validator explains a mismatch to an
operator -- "wrong range" and "too specific" are different failures with
different remedies.
"""

from __future__ import annotations

from ipaddress import ip_network

from .roa import Roa


def covers(roa_prefix: str, announced_prefix: str) -> bool:
    """Is the announced address range wholly contained in the ROA's address range?

    subnet_of() answers a pure address-range question: every address in
    announced_prefix must also be an address in roa_prefix. This says nothing
    about specificity (max_length) -- a /8 ROA "covers" a /24 announcement in
    this sense even if the ROA never authorized anything narrower than /9.
    That's why within_max_length() below is a second, separate check.
    """
    roa_net = ip_network(roa_prefix)
    announced_net = ip_network(announced_prefix)
    return announced_net.subnet_of(roa_net)


def within_max_length(announced_prefix: str, max_length: int) -> bool:
    """Is the announcement's prefix length no more specific than the ROA allows?

    Deliberately explicit rather than folded into covers(): prefixlen <= max_length,
    nothing else. A /24 announcement under a ROA with max_length 23 fails this
    even though it may pass covers() -- that combination is exactly what an
    INVALID_MAX_LENGTH-flavored verdict in validate.py is for.
    """
    return ip_network(announced_prefix).prefixlen <= max_length


def find_covering_roas(roas: tuple[Roa, ...], announced_prefix: str) -> tuple[Roa, ...]:
    """Filter to the ROAs whose address range covers this announcement (range only, not length)."""
    return tuple(roa for roa in roas if covers(roa.prefix, announced_prefix))
