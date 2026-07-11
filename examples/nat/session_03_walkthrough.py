from protocol_in_code.nat.five_tuple import FiveTuple, reply_tuple
from protocol_in_code.nat.table import ConntrackTable, MatchDirection, NatEntry, insert, match, remove


def main() -> None:
    print("Session 03 walkthrough: The reply finds its way back")
    print()

    table = ConntrackTable()

    original = FiveTuple(protocol="tcp", src_ip="10.0.0.5", src_port=51000, dst_ip="93.184.216.34", dst_port=443)
    translated = FiveTuple(protocol="tcp", src_ip="203.0.113.9", src_port=40000, dst_ip="93.184.216.34", dst_port=443)
    entry = NatEntry(original=original, translated=translated, created_at=0)

    insert(table, entry)
    two_keys = len(table.entries) == 2
    marker = "OK" if two_keys else "NG"
    print(f"[{marker}] one insert writes two keys   -> {len(table.entries)} entries in the table")

    forward = match(table, original)
    marker = "OK" if forward.direction is MatchDirection.FORWARD else "NG"
    print(f"[{marker}] original tuple matches       -> {forward.direction.value}")

    reply_of_translated = reply_tuple(translated)
    reverse = match(table, reply_of_translated)
    marker = "OK" if reverse.direction is MatchDirection.REVERSE else "NG"
    print(f"[{marker}] reply-of-translated matches  -> {reverse.direction.value} (pre-computed at insert time)")

    same_entry = forward.entry is reverse.entry
    marker = "OK" if same_entry else "NG"
    print(f"[{marker}] both directions, one entry   -> forward.entry is reverse.entry")

    unrelated = FiveTuple(protocol="tcp", src_ip="198.51.100.7", src_port=12345, dst_ip="203.0.113.9", dst_port=40000)
    no_match = match(table, unrelated)
    marker = "OK" if no_match.direction is MatchDirection.NO_MATCH else "NG"
    print(f"[{marker}] unrelated tuple misses       -> {no_match.direction.value}")

    remove(table, entry)
    both_gone = original not in table.entries and reply_of_translated not in table.entries
    marker = "OK" if both_gone else "NG"
    print(f"[{marker}] remove deletes both keys     -> {len(table.entries)} entries left")

    after_removal = match(table, original)
    marker = "OK" if after_removal.direction is MatchDirection.NO_MATCH else "NG"
    print(f"[{marker}] forward direction now misses -> {after_removal.direction.value}")


if __name__ == "__main__":
    main()
