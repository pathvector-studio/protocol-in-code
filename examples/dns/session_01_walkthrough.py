from protocol_in_code.dns.query import DNSQuestion, QuestionValidity, question_key, validate_question


SCENARIOS = (
    (
        "empty name",
        DNSQuestion(qname=""),
        QuestionValidity.EMPTY_NAME,
    ),
    (
        "empty label",
        DNSQuestion(qname="www..example.com"),
        QuestionValidity.EMPTY_LABEL,
    ),
    (
        "label too long",
        DNSQuestion(qname="a" * 64 + ".example.com"),
        QuestionValidity.LABEL_TOO_LONG,
    ),
    (
        "name too long",
        DNSQuestion(qname=".".join(["a" * 60] * 5)),
        QuestionValidity.NAME_TOO_LONG,
    ),
    (
        "unsupported type",
        DNSQuestion(qname="example.com", qtype="LOC"),
        QuestionValidity.UNSUPPORTED_TYPE,
    ),
    (
        "unsupported class",
        DNSQuestion(qname="example.com", qclass="CH"),
        QuestionValidity.UNSUPPORTED_CLASS,
    ),
    (
        "valid question",
        DNSQuestion(qname="WWW.Example.COM."),
        QuestionValidity.VALID,
    ),
)


def main() -> None:
    print("Session 01 walkthrough: A query is a question object")
    print()
    for name, question, expected in SCENARIOS:
        result = validate_question(question)
        marker = "OK" if result is expected else "NG"
        print(f"[{marker}] {name:24s} -> {result.value:18s} (expected {expected.value})")

    print()
    same_a = question_key(DNSQuestion(qname="WWW.Example.COM."))
    same_b = question_key(DNSQuestion(qname="www.example.com"))
    marker = "OK" if same_a == same_b else "NG"
    print(f"[{marker}] two spellings, one key   -> {same_a}")


if __name__ == "__main__":
    main()
