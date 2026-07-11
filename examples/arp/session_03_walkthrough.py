from protocol_in_code.arp.cache import NeighborCache, NeighborState, lookup, start_resolution
from protocol_in_code.arp.gratuitous import AcceptPolicy, ArpAnnouncement, ProcessOutcome, process_announcement


def main() -> None:
    print("Session 03 walkthrough: Anyone can answer")
    print()

    # A brand-new entry: both policies let a gratuitous announcement create it.
    accept_cache = NeighborCache()
    new_entry = ArpAnnouncement(ip="10.0.0.5", mac="AA:BB:CC:00:00:05", is_reply_to_us=False)
    created_accept = process_announcement(accept_cache, new_entry, now=0, policy=AcceptPolicy.ACCEPT_ALL)
    marker = "OK" if created_accept is ProcessOutcome.CREATED else "NG"
    print(f"[{marker}] new entry under ACCEPT_ALL     -> {created_accept.value}")

    known_cache = NeighborCache()
    created_known = process_announcement(known_cache, new_entry, now=0, policy=AcceptPolicy.ONLY_IF_KNOWN)
    marker = "OK" if created_known is ProcessOutcome.CREATED else "NG"
    print(f"[{marker}] new entry under ONLY_IF_KNOWN  -> {created_known.value}")

    # The poisoning surface: an unsolicited announcement overwrites a KNOWN mapping under ACCEPT_ALL.
    victim_cache = NeighborCache()
    process_announcement(
        victim_cache,
        ArpAnnouncement(ip="10.0.0.7", mac="AA:BB:CC:00:00:07", is_reply_to_us=True),
        now=0,
        policy=AcceptPolicy.ACCEPT_ALL,
    )
    spoof = ArpAnnouncement(ip="10.0.0.7", mac="EE:EE:EE:00:00:66", is_reply_to_us=False)
    poisoned = process_announcement(victim_cache, spoof, now=10, policy=AcceptPolicy.ACCEPT_ALL)
    poisoned_mac = lookup(victim_cache, "10.0.0.7", now=10).mac
    marker = "OK" if poisoned is ProcessOutcome.OVERWROTE and poisoned_mac == "EE:EE:EE:00:00:66" else "NG"
    print(f"[{marker}] unsolicited overwrite (ACCEPT_ALL, poisoning surface) -> {poisoned.value} mac={poisoned_mac}")

    # The mitigation: ONLY_IF_KNOWN refuses the same unsolicited overwrite; mac is unchanged.
    defended_cache = NeighborCache()
    process_announcement(
        defended_cache,
        ArpAnnouncement(ip="10.0.0.7", mac="AA:BB:CC:00:00:07", is_reply_to_us=True),
        now=0,
        policy=AcceptPolicy.ONLY_IF_KNOWN,
    )
    refused = process_announcement(defended_cache, spoof, now=10, policy=AcceptPolicy.ONLY_IF_KNOWN)
    defended_mac = lookup(defended_cache, "10.0.0.7", now=10).mac
    marker = "OK" if refused is ProcessOutcome.REFUSED_UNSOLICITED and defended_mac == "AA:BB:CC:00:00:07" else "NG"
    print(f"[{marker}] same announcement under ONLY_IF_KNOWN -> {refused.value} mac={defended_mac} (unchanged)")

    # CONFIRMED: a solicited reply repeating the same mac we already trusted.
    reply_cache = NeighborCache()
    process_announcement(
        reply_cache,
        ArpAnnouncement(ip="10.0.0.9", mac="AA:BB:CC:00:00:09", is_reply_to_us=True),
        now=0,
        policy=AcceptPolicy.ONLY_IF_KNOWN,
    )
    same_reply = ArpAnnouncement(ip="10.0.0.9", mac="AA:BB:CC:00:00:09", is_reply_to_us=True)
    confirmed = process_announcement(reply_cache, same_reply, now=5, policy=AcceptPolicy.ONLY_IF_KNOWN)
    marker = "OK" if confirmed is ProcessOutcome.CONFIRMED else "NG"
    print(f"[{marker}] reply-to-us repeating the known mac -> {confirmed.value}")

    # An in-flight resolution (INCOMPLETE) always confirms too, even though it's unsolicited --
    # but the outcome reads OVERWROTE, because an INCOMPLETE entry's mac is None and None never
    # equals the announced mac. "Overwrote" here means "went from no mac to a mac," not malice.
    inflight_cache = NeighborCache()
    start_resolution(inflight_cache, "10.0.0.11", now=0)
    inflight_reply = ArpAnnouncement(ip="10.0.0.11", mac="AA:BB:CC:00:00:11", is_reply_to_us=False)
    gleaned = process_announcement(inflight_cache, inflight_reply, now=1, policy=AcceptPolicy.ONLY_IF_KNOWN)
    gleaned_result = lookup(inflight_cache, "10.0.0.11", now=1)
    marker = "OK" if gleaned is ProcessOutcome.OVERWROTE and gleaned_result.state is NeighborState.REACHABLE and gleaned_result.mac == "AA:BB:CC:00:00:11" else "NG"
    print(f"[{marker}] unsolicited reply while INCOMPLETE  -> {gleaned.value} state={gleaned_result.state.value} mac={gleaned_result.mac}")


if __name__ == "__main__":
    main()
