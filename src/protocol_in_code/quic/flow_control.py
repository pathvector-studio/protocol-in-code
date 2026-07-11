from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# The MAX_DATA / MAX_STREAM_DATA credit model follows RFC 9000 section 4 (Flow Control):
# a receiver grants a limit, a sender consumes against it, and the limit only ever moves up.


class SendDecision(str, Enum):
    SENT = "Sent"
    BLOCKED_BY_STREAM = "BlockedByStream"
    BLOCKED_BY_CONNECTION = "BlockedByConnection"


@dataclass
class CreditAccount:
    """One shape, two levels: the same credit balance backs both a stream and the connection."""

    limit: int
    consumed: int = 0


def can_send(account: CreditAccount, n: int) -> bool:
    return account.consumed + n <= account.limit


def consume(account: CreditAccount, n: int) -> None:
    account.consumed += n


def grant(account: CreditAccount, new_limit: int) -> None:
    """MAX_DATA/MAX_STREAM_DATA only ever raises the limit; a lower value is simply ignored."""
    if new_limit > account.limit:
        account.limit = new_limit


def send_on_stream(
    conn_account: CreditAccount, stream_account: CreditAccount, n: int
) -> SendDecision:
    """Two-level check: a send needs room on both its stream and the shared connection."""
    if not can_send(stream_account, n):
        return SendDecision.BLOCKED_BY_STREAM

    if not can_send(conn_account, n):
        return SendDecision.BLOCKED_BY_CONNECTION

    consume(stream_account, n)
    consume(conn_account, n)
    return SendDecision.SENT


if __name__ == "__main__":
    conn_account = CreditAccount(limit=100)
    stream_account = CreditAccount(limit=1000)

    sent = send_on_stream(conn_account, stream_account, 60)
    assert sent is SendDecision.SENT
    assert conn_account.consumed == 60
    assert stream_account.consumed == 60

    # Connection credit is nearly exhausted (40 left) while the stream still has plenty (940):
    # the stream-level check alone would allow this send, so BLOCKED_BY_CONNECTION proves
    # the connection-level check runs too, not just the stream-level one.
    blocked_by_conn = send_on_stream(conn_account, stream_account, 50)
    assert blocked_by_conn is SendDecision.BLOCKED_BY_CONNECTION
    assert conn_account.consumed == 60  # unchanged: nothing was actually sent

    grant(conn_account, 200)
    assert conn_account.limit == 200
    grant(conn_account, 150)  # a lower grant is ignored: limits only move up
    assert conn_account.limit == 200

    now_fits = send_on_stream(conn_account, stream_account, 50)
    assert now_fits is SendDecision.SENT

    tight_stream = CreditAccount(limit=10)
    blocked_by_stream = send_on_stream(conn_account, tight_stream, 20)
    assert blocked_by_stream is SendDecision.BLOCKED_BY_STREAM

    print("[OK] flow_control.py")
