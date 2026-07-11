from protocol_in_code.quic.flow_control import CreditAccount, SendDecision, grant, send_on_stream


def main() -> None:
    print("Session 09 walkthrough: Flow control is a credit balance")
    print()

    conn_account = CreditAccount(limit=100)
    stream_account = CreditAccount(limit=1000)

    sent = send_on_stream(conn_account, stream_account, 60)
    marker = "OK" if sent is SendDecision.SENT and conn_account.consumed == 60 and stream_account.consumed == 60 else "NG"
    print(f"[{marker}] send within both limits          -> {sent.value} conn={conn_account.consumed} stream={stream_account.consumed}")

    tight_stream = CreditAccount(limit=10)
    blocked_stream = send_on_stream(conn_account, tight_stream, 20)
    marker = "OK" if blocked_stream is SendDecision.BLOCKED_BY_STREAM and tight_stream.consumed == 0 and conn_account.consumed == 60 else "NG"
    print(f"[{marker}] stream credit exhausted           -> {blocked_stream.value}  <- nothing consumed on either account")

    blocked_conn = send_on_stream(conn_account, stream_account, 50)
    marker = "OK" if blocked_conn is SendDecision.BLOCKED_BY_CONNECTION and conn_account.consumed == 60 and stream_account.consumed == 60 else "NG"
    print(f"[{marker}] ample stream, tight connection    -> {blocked_conn.value}  <- stream check passed, connection check failed")

    grant(conn_account, 200)
    marker = "OK" if conn_account.limit == 200 else "NG"
    print(f"[{marker}] grant raises connection limit     -> limit={conn_account.limit}")

    now_fits = send_on_stream(conn_account, stream_account, 50)
    marker = "OK" if now_fits is SendDecision.SENT and conn_account.consumed == 110 else "NG"
    print(f"[{marker}] same send now goes through        -> {now_fits.value} conn={conn_account.consumed}")

    grant(conn_account, 150)
    marker = "OK" if conn_account.limit == 200 else "NG"
    print(f"[{marker}] lower grant is ignored             -> limit={conn_account.limit}  <- monotonic: limits only move up")


if __name__ == "__main__":
    main()
