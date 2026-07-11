from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .cache import NeighborCache, NeighborState, confirm

# The security lesson of the track: ARP has no authentication. Any host on the
# segment can send an announcement claiming an IP-to-MAC mapping, solicited or
# not, and nothing in the protocol proves the claim. Under ACCEPT_ALL that
# means an unsolicited announcement can OVERWRITE an entry the cache already
# trusted — this is the ARP spoofing / cache poisoning surface, plainly: an
# attacker who can put frames on the wire can redirect traffic meant for
# someone else. ONLY_IF_KNOWN is a crude, honestly-labeled defense in the
# spirit of Dynamic ARP Inspection: it still lets a gratuitous announcement
# populate a *new* entry, but refuses to let an unsolicited one clobber a
# mapping already learned. That's a mitigation, not a fix — DAI in real
# switches also needs a trusted binding table (e.g. from DHCP snooping) to be
# meaningful; this toy version only shows the shape of the defense.


class AcceptPolicy(str, Enum):
    ACCEPT_ALL = "AcceptAll"
    ONLY_IF_KNOWN = "OnlyIfKnown"


class ProcessOutcome(str, Enum):
    CREATED = "Created"
    CONFIRMED = "Confirmed"
    OVERWROTE = "Overwrote"
    REFUSED_UNSOLICITED = "RefusedUnsolicited"


@dataclass(frozen=True)
class ArpAnnouncement:
    ip: str
    mac: str
    is_reply_to_us: bool


def process_announcement(
    cache: NeighborCache,
    announcement: ArpAnnouncement,
    now: int,
    policy: AcceptPolicy,
) -> ProcessOutcome:
    """Decide what an announcement is allowed to do to the cache: ARP itself never asks permission."""
    existing = cache.entries.get(announcement.ip)

    if existing is None:
        confirm(cache, announcement.ip, announcement.mac, now)
        return ProcessOutcome.CREATED

    if announcement.is_reply_to_us or existing.state is NeighborState.INCOMPLETE:
        confirm(cache, announcement.ip, announcement.mac, now)
        if existing.mac == announcement.mac:
            return ProcessOutcome.CONFIRMED
        return ProcessOutcome.OVERWROTE

    if policy is AcceptPolicy.ONLY_IF_KNOWN:
        return ProcessOutcome.REFUSED_UNSOLICITED

    confirm(cache, announcement.ip, announcement.mac, now)
    if existing.mac == announcement.mac:
        return ProcessOutcome.CONFIRMED
    return ProcessOutcome.OVERWROTE
