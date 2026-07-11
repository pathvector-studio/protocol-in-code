from protocol_in_code.tcp.segment import Segment, SegmentValidity, flags_label, validate_segment


def main() -> None:
    print("Session 01 walkthrough: A segment carries the conversation state")
    print()

    valid = Segment(seq=1000, ack=0, flags=frozenset({"SYN"}), payload_len=0)
    valid_result = validate_segment(valid)
    marker = "OK" if valid_result is SegmentValidity.VALID else "NG"
    print(f"[{marker}] SYN, no payload            -> {valid_result.value}")

    valid_data = Segment(seq=1000, ack=2000, flags=frozenset({"ACK"}), payload_len=50)
    valid_data_result = validate_segment(valid_data)
    marker = "OK" if valid_data_result is SegmentValidity.VALID else "NG"
    print(f"[{marker}] ACK carrying 50 bytes       -> {valid_data_result.value}")

    bad_flag = Segment(seq=1000, ack=0, flags=frozenset({"SYN", "URG"}), payload_len=0)
    bad_flag_result = validate_segment(bad_flag)
    marker = "OK" if bad_flag_result is SegmentValidity.BAD_FLAG_NAME else "NG"
    print(f"[{marker}] unknown flag 'URG'          -> {bad_flag_result.value}")

    syn_fin = Segment(seq=1000, ack=0, flags=frozenset({"SYN", "FIN"}), payload_len=0)
    syn_fin_result = validate_segment(syn_fin)
    marker = "OK" if syn_fin_result is SegmentValidity.SYN_FIN_TOGETHER else "NG"
    print(f"[{marker}] SYN and FIN together        -> {syn_fin_result.value}")

    negative_len = Segment(seq=1000, ack=0, flags=frozenset(), payload_len=-1)
    negative_len_result = validate_segment(negative_len)
    marker = "OK" if negative_len_result is SegmentValidity.NEGATIVE_LENGTH else "NG"
    print(f"[{marker}] payload_len -1              -> {negative_len_result.value}")

    rst_with_payload = Segment(seq=1000, ack=0, flags=frozenset({"RST"}), payload_len=10)
    rst_with_payload_result = validate_segment(rst_with_payload)
    marker = "OK" if rst_with_payload_result is SegmentValidity.PAYLOAD_WITHOUT_SEQ_MEANING else "NG"
    print(f"[{marker}] RST carrying a payload      -> {rst_with_payload_result.value}")

    label = flags_label(valid_data)
    marker = "OK" if label == "ACK" else "NG"
    print(f"[{marker}] flags_label on ACK segment  -> '{label}'")

    combo_label = flags_label(syn_fin)
    marker = "OK" if combo_label == "SYN,FIN" else "NG"
    print(f"[{marker}] flags_label keeps wire order -> '{combo_label}'")


if __name__ == "__main__":
    main()
