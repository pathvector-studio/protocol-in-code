from protocol_in_code.tcp2.syn_cookies import (
    MSS_TABLE,
    CookieVerdict,
    encode_cookie,
    verify_cookie,
)


def main() -> None:
    print("Session 02 walkthrough: SYN cookies are stateless memory")
    print()

    secret = "server-secret-do-not-log"
    other_secret = "a-different-server-secret"
    src_ip, src_port = "203.0.113.5", 51000
    dst_ip, dst_port = "198.51.100.7", 443
    mss_index = MSS_TABLE.index(1460)
    counter = 5

    cookie = encode_cookie(secret, src_ip, src_port, dst_ip, dst_port, mss_index, counter)

    round_trip = verify_cookie(cookie, secret, src_ip, src_port, dst_ip, dst_port, current_counter=counter)
    marker = "OK" if round_trip.verdict is CookieVerdict.VALID and round_trip.recovered_mss == 1460 else "NG"
    print(f"[{marker}] encode -> verify, same counter        -> {round_trip.verdict.value}, recovered_mss={round_trip.recovered_mss}")

    marker = "OK" if round_trip.recovered_mss in MSS_TABLE else "NG"
    print(f"[{marker}] recovered_mss is one of MSS_TABLE      -> {round_trip.recovered_mss} in {MSS_TABLE}")

    tampered_cookie = cookie ^ (1 << 20)  # flip a bit inside the 25-bit hash region
    tampered = verify_cookie(tampered_cookie, secret, src_ip, src_port, dst_ip, dst_port, current_counter=counter)
    marker = "OK" if tampered.verdict is CookieVerdict.TAMPERED else "NG"
    print(f"[{marker}] flip a hash bit                        -> {tampered.verdict.value}")

    stale = verify_cookie(cookie, secret, src_ip, src_port, dst_ip, dst_port, current_counter=counter + 3)
    marker = "OK" if stale.verdict is CookieVerdict.STALE_COUNTER else "NG"
    print(f"[{marker}] verify 3 ticks later (max_age=2)       -> {stale.verdict.value}")

    still_fresh = verify_cookie(cookie, secret, src_ip, src_port, dst_ip, dst_port, current_counter=counter + 2)
    marker = "OK" if still_fresh.verdict is CookieVerdict.VALID else "NG"
    print(f"[{marker}] verify exactly 2 ticks later (== max_age) -> {still_fresh.verdict.value}")

    wrong_secret = verify_cookie(cookie, other_secret, src_ip, src_port, dst_ip, dst_port, current_counter=counter)
    marker = "OK" if wrong_secret.verdict is not CookieVerdict.VALID else "NG"
    print(f"[{marker}] a different secret never verifies      -> {wrong_secret.verdict.value} (proof, not a lookup)")


if __name__ == "__main__":
    main()
