from protocol_in_code.dns.referral import (
    ResourceRecord,
    ResponseKind,
    ServerResponse,
    classify_response,
    referral_targets,
)


SCENARIOS = (
    (
        "answer with records",
        ServerResponse(
            answer_records=(ResourceRecord("www.example.com", "A", "192.0.2.10"),),
            is_authoritative=True,
        ),
        ResponseKind.ANSWER,
    ),
    (
        "referral to child servers",
        ServerResponse(
            authority_ns=("a.gtld-servers.net", "b.gtld-servers.net"),
        ),
        ResponseKind.REFERRAL,
    ),
    (
        "authoritative empty answer",
        ServerResponse(
            authority_ns=("ns1.example.com",),
            is_authoritative=True,
        ),
        ResponseKind.NODATA,
    ),
    (
        "name does not exist",
        ServerResponse(rcode="NXDOMAIN"),
        ResponseKind.NAME_ERROR,
    ),
    (
        "server broke",
        ServerResponse(rcode="SERVFAIL"),
        ResponseKind.SERVER_FAILURE,
    ),
)


def main() -> None:
    print("Session 03 walkthrough: Delegation is a referral, not an answer")
    print()
    for name, response, expected in SCENARIOS:
        result = classify_response(response)
        marker = "OK" if result is expected else "NG"
        print(f"[{marker}] {name:28s} -> {result.value:14s} (expected {expected.value})")

    print()
    referral = ServerResponse(authority_ns=("a.gtld-servers.net", "b.gtld-servers.net"))
    answer = ServerResponse(
        answer_records=(ResourceRecord("www.example.com", "A", "192.0.2.10"),),
        is_authoritative=True,
    )
    marker = "OK" if referral_targets(referral) == ("a.gtld-servers.net", "b.gtld-servers.net") else "NG"
    print(f"[{marker}] referral gives next servers -> {referral_targets(referral)}")
    marker = "OK" if referral_targets(answer) == () else "NG"
    print(f"[{marker}] answer gives no next servers -> {referral_targets(answer)}")


if __name__ == "__main__":
    main()
