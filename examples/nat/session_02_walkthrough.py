from protocol_in_code.nat.five_tuple import FiveTuple
from protocol_in_code.nat.rewrite import Packet, RewriteKind, RewriteSpec, apply, apply_dnat, apply_snat


def main() -> None:
    print("Session 02 walkthrough: Translation is a rewrite function")
    print()

    original_tuple = FiveTuple(protocol="tcp", src_ip="10.0.0.5", src_port=51000, dst_ip="93.184.216.34", dst_port=443)
    packet = Packet(tuple=original_tuple, payload_note="SYN")

    snatted = apply_snat(packet, new_src_ip="203.0.113.9", new_src_port=40000)
    src_changed = snatted.tuple.src_ip == "203.0.113.9" and snatted.tuple.src_port == 40000
    marker = "OK" if src_changed else "NG"
    print(f"[{marker}] SNAT rewrites src fields     -> {snatted.tuple.src_ip}:{snatted.tuple.src_port}")

    dst_untouched = snatted.tuple.dst_ip == original_tuple.dst_ip and snatted.tuple.dst_port == original_tuple.dst_port
    marker = "OK" if dst_untouched else "NG"
    print(f"[{marker}] SNAT leaves dst fields alone -> {snatted.tuple.dst_ip}:{snatted.tuple.dst_port}")

    dnatted = apply_dnat(packet, new_dst_ip="10.0.0.100", new_dst_port=8080)
    dst_changed = dnatted.tuple.dst_ip == "10.0.0.100" and dnatted.tuple.dst_port == 8080
    marker = "OK" if dst_changed else "NG"
    print(f"[{marker}] DNAT rewrites dst fields     -> {dnatted.tuple.dst_ip}:{dnatted.tuple.dst_port}")

    src_untouched = dnatted.tuple.src_ip == original_tuple.src_ip and dnatted.tuple.src_port == original_tuple.src_port
    marker = "OK" if src_untouched else "NG"
    print(f"[{marker}] DNAT leaves src fields alone -> {dnatted.tuple.src_ip}:{dnatted.tuple.src_port}")

    unchanged = packet.tuple == original_tuple and packet.payload_note == "SYN"
    marker = "OK" if unchanged else "NG"
    print(f"[{marker}] input packet is untouched    -> frozen in, frozen out")

    snat_spec = RewriteSpec(kind=RewriteKind.SNAT, ip="203.0.113.9", port=40000)
    dispatched_snat = apply(packet, snat_spec)
    marker = "OK" if dispatched_snat == snatted else "NG"
    print(f"[{marker}] apply() dispatches to SNAT   -> {dispatched_snat.tuple.src_ip}:{dispatched_snat.tuple.src_port}")

    dnat_spec = RewriteSpec(kind=RewriteKind.DNAT, ip="10.0.0.100", port=8080)
    dispatched_dnat = apply(packet, dnat_spec)
    marker = "OK" if dispatched_dnat == dnatted else "NG"
    print(f"[{marker}] apply() dispatches to DNAT   -> {dispatched_dnat.tuple.dst_ip}:{dispatched_dnat.tuple.dst_port}")


if __name__ == "__main__":
    main()
