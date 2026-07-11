from protocol_in_code.tls.record import UnprotectOutcome, protect, unprotect


def main() -> None:
    print("Session 07 walkthrough: The record layer is an envelope")
    print()

    key = "traffic-secret-abc"
    record = protect("hello server", key, seq=0)

    opened = unprotect(record, key)
    marker = "OK" if opened.outcome is UnprotectOutcome.OK and opened.plaintext == "hello server" else "NG"
    print(f"[{marker}] protect -> unprotect round-trips  -> {opened.outcome.value} {opened.plaintext!r}")

    header_visible = record.content_type == "application_data" and record.seq == 0
    marker = "OK" if header_visible else "NG"
    print(f"[{marker}] header stays readable on the wire  -> content_type={record.content_type} seq={record.seq}")

    tampered = protect("hello server", key, seq=0)
    tampered = type(tampered)(
        content_type=tampered.content_type,
        seq=tampered.seq,
        ciphertext="hello attacker",
        tag=tampered.tag,
    )
    tampered_result = unprotect(tampered, key)
    marker = "OK" if tampered_result.outcome is UnprotectOutcome.BAD_TAG and tampered_result.plaintext is None else "NG"
    print(f"[{marker}] tampered ciphertext -> BAD_TAG      -> {tampered_result.outcome.value} {tampered_result.plaintext!r}")

    wrong_key_result = unprotect(record, "a-different-key")
    marker = "OK" if wrong_key_result.outcome is UnprotectOutcome.BAD_TAG else "NG"
    print(f"[{marker}] wrong key -> BAD_TAG (not WRONG_KEY) -> {wrong_key_result.outcome.value}")

    replayed = protect("hello server", key, seq=0)
    reordered = type(replayed)(
        content_type=replayed.content_type,
        seq=5,
        ciphertext=replayed.ciphertext,
        tag=replayed.tag,
    )
    replay_result = unprotect(reordered, key)
    marker = "OK" if replay_result.outcome is UnprotectOutcome.BAD_TAG else "NG"
    print(f"[{marker}] wrong seq (replay/reorder) -> BAD_TAG -> {replay_result.outcome.value}")

    second_record = protect("second message", key, seq=1)
    second_opened = unprotect(second_record, key)
    marker = "OK" if second_opened.outcome is UnprotectOutcome.OK and second_opened.plaintext == "second message" else "NG"
    print(f"[{marker}] next seq protects independently   -> {second_opened.outcome.value} {second_opened.plaintext!r}")


if __name__ == "__main__":
    main()
