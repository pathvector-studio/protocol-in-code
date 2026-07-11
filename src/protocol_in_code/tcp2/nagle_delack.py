from __future__ import annotations

from dataclasses import dataclass

# All times in this file are milliseconds, matching tcp/rto.py's _MS convention -
# delayed ACK and Nagle are both timer-driven, and the timer that matters (200ms)
# is fine-grained enough that whole-second ticks would hide the interaction.
DELACK_TIMEOUT_MS = 200

# The event stream uses one sentinel value instead of a second parameter: a write
# is a positive byte count, and READ marks the moment the application blocks
# waiting for a reply. This keeps `writes` a single flat tuple, as specified,
# while still letting a "write-write-read" pattern be written literally as
# (small, small, READ).
READ = -1


@dataclass(frozen=True)
class Timeline:
    events: tuple[str, ...]
    total_ms: int


def simulate(writes: tuple[int, ...], nodelay: bool) -> Timeline:
    """Play out one Nagle/delayed-ACK interaction and report whether it stalls.

    Nagle (sender side): while there is unacked data in flight, a *small* subsequent
    write is held rather than sent immediately - the idea is to coalesce tiny writes
    into fewer, fuller segments. Delayed ACK (receiver side): a single arriving segment
    doesn't get an immediate ACK; the receiver waits up to DELACK_TIMEOUT_MS hoping a
    second segment (or the application's own reply) will let it piggyback the ACK for
    free. Each rule is a reasonable optimization in isolation. Together: sender holds
    segment #2 waiting for the ACK of segment #1, and receiver holds that very ACK
    waiting for segment #2. Nobody sends anything until the delayed-ACK timer finally
    expires - a 200ms stall for what should have been an instant round trip. Setting
    TCP_NODELAY disables Nagle on the sender, breaking the deadlock: segment #2 goes
    out immediately, so the receiver has two segments to piggyback the ACK on and never
    needs its timer.
    """
    events: list[str] = []
    clock_ms = 0
    unacked_segment = False   # sender has one segment out with no ACK yet
    pending_ack = False       # receiver holds an ACK, waiting for a second segment or timeout
    held_write: int | None = None

    for item in writes:
        if item == READ:
            if pending_ack:
                # The receiver's ACK is still parked, and any second segment that could
                # have piggybacked on it is itself stuck behind Nagle (held_write) waiting
                # for that very ACK - a genuine deadlock, broken only by the delayed-ACK
                # timer finally giving up and sending the ACK on its own.
                clock_ms += DELACK_TIMEOUT_MS
                events.append(f"delayed-ack timeout fires at {clock_ms}ms, ack sent")
                pending_ack = False
                unacked_segment = False
                if held_write is not None:
                    events.append(f"nagle releases held write({held_write}) at {clock_ms}ms")
                    held_write = None
            events.append(f"application read completes at {clock_ms}ms")
            continue

        write_len = item
        if unacked_segment and not nodelay:
            # Nagle: a segment is already unacked, so this small write is held rather
            # than sent - it will go out once the pending ACK arrives.
            held_write = write_len
            events.append(f"write({write_len}) held by nagle at {clock_ms}ms, unacked segment in flight")
            continue

        events.append(f"write({write_len}) sent as segment at {clock_ms}ms")
        unacked_segment = True

        if pending_ack:
            # A second segment arrived at the receiver while an ACK was already pending:
            # piggyback both acks onto one, sent immediately, no timer needed.
            events.append(f"second segment lets receiver ack immediately at {clock_ms}ms")
            pending_ack = False
            unacked_segment = False
            if held_write is not None:
                events.append(f"nagle releases held write({held_write}) at {clock_ms}ms")
                held_write = None
        else:
            pending_ack = True

    return Timeline(events=tuple(events), total_ms=clock_ms)
