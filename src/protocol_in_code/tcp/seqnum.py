from __future__ import annotations

SEQ_SPACE = 2**32


def seq_add(a: int, n: int) -> int:
    """Sequence numbers live on a ring: adding past the top wraps back to zero."""
    return (a + n) % SEQ_SPACE


def seq_lt(a: int, b: int) -> bool:
    """Is a 'before' b on the ring? The signed-difference trick: half the ring is 'ahead'."""
    return (b - a) % SEQ_SPACE < SEQ_SPACE // 2 and a != b


def seq_le(a: int, b: int) -> bool:
    return a == b or seq_lt(a, b)


def in_receive_window(seq: int, rcv_nxt: int, window: int) -> bool:
    """A seq is acceptable if it falls in [rcv_nxt, rcv_nxt + window), wrap included."""
    if window <= 0:
        return seq == rcv_nxt
    offset = (seq - rcv_nxt) % SEQ_SPACE
    return offset < window
