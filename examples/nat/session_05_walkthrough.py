from protocol_in_code.nat.five_tuple import FiveTuple, reply_tuple
from protocol_in_code.nat.table import ConntrackTable, NatEntry, insert
from protocol_in_code.nat.timeout import EXPIRY_SECONDS, is_expired, sweep, touch


def main() -> None:
    print("Session 05 walkthrough: State expires, again")
    print()

    tcp_original = FiveTuple(protocol="tcp", src_ip="10.0.0.5", src_port=51000, dst_ip="93.184.216.34", dst_port=443)
    tcp_translated = FiveTuple(protocol="tcp", src_ip="203.0.113.9", src_port=49152, dst_ip="93.184.216.34", dst_port=443)
    tcp_entry = NatEntry(original=tcp_original, translated=tcp_translated, created_at=0)

    udp_original = FiveTuple(protocol="udp", src_ip="10.0.0.6", src_port=51001, dst_ip="8.8.8.8", dst_port=53)
    udp_translated = FiveTuple(protocol="udp", src_ip="203.0.113.9", src_port=49153, dst_ip="8.8.8.8", dst_port=53)
    udp_entry = NatEntry(original=udp_original, translated=udp_translated, created_at=0)

    tcp_alive = not is_expired(tcp_entry, now=299)
    marker = "OK" if tcp_alive else "NG"
    print(f"[{marker}] tcp entry at 299s (limit {EXPIRY_SECONDS['tcp']}s) -> alive")

    tcp_dead = is_expired(tcp_entry, now=300)
    marker = "OK" if tcp_dead else "NG"
    print(f"[{marker}] tcp entry at exactly 300s          -> expired")

    udp_dead = is_expired(udp_entry, now=30)
    marker = "OK" if udp_dead else "NG"
    print(f"[{marker}] udp entry at exactly 30s (10x shorter than tcp) -> expired")

    table = ConntrackTable()
    insert(table, tcp_entry)
    insert(table, udp_entry)
    keys_before = len(table.entries)
    marker = "OK" if keys_before == 4 else "NG"
    print(f"[{marker}] two entries inserted, two keys each -> {keys_before} keys in table")

    removed = sweep(table, now=300)
    marker = "OK" if set(removed) == {tcp_original, udp_original} else "NG"
    print(f"[{marker}] sweep at 300s removes both flows   -> sweep returned {len(removed)} original tuples")

    keys_after = len(table.entries)
    marker = "OK" if keys_after == 0 else "NG"
    print(f"[{marker}] sweep deletes both keys per entry   -> {keys_after} keys remain")

    fresh_udp = NatEntry(original=udp_original, translated=udp_translated, created_at=0)
    table2 = ConntrackTable()
    insert(table2, fresh_udp)

    touched = touch(fresh_udp, now=25)
    table2.entries[touched.original] = touched
    table2.entries[reply_tuple(touched.translated)] = touched

    survives_old_deadline = not is_expired(touched, now=30)
    marker = "OK" if survives_old_deadline else "NG"
    print(f"[{marker}] touch() resets created_at, survives old 30s deadline -> alive at now=30")

    dies_at_new_deadline = is_expired(touched, now=55)
    marker = "OK" if dies_at_new_deadline else "NG"
    print(f"[{marker}] touched entry dies at its new deadline (25 + 30)    -> expired at now=55")

    unchanged = fresh_udp.created_at == 0 and touched.created_at == 25 and touched is not fresh_udp
    marker = "OK" if unchanged else "NG"
    print(f"[{marker}] touch() returns a new frozen entry, original untouched -> created_at {fresh_udp.created_at} vs {touched.created_at}")


if __name__ == "__main__":
    main()
