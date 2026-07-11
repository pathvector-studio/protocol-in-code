from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# Stream states and the legal transitions between them follow RFC 9113 section 5.1
# (Stream States), simplified to the subset a server-side toy connection needs.


class StreamState(str, Enum):
    IDLE = "Idle"
    OPEN = "Open"
    HALF_CLOSED_REMOTE = "HalfClosedRemote"
    CLOSED = "Closed"


class FrameOutcome(str, Enum):
    ACCEPTED = "Accepted"
    STREAM_OPENED = "StreamOpened"
    STREAM_HALF_CLOSED = "StreamHalfClosed"
    STREAM_CLOSED = "StreamClosed"
    ERROR_DATA_ON_IDLE_STREAM = "ErrorDataOnIdleStream"
    ERROR_FRAME_AFTER_CLOSED = "ErrorFrameAfterClosed"


@dataclass(frozen=True)
class Frame:
    stream_id: int
    frame_type: str  # "HEADERS" or "DATA"
    payload_len: int
    end_stream: bool


@dataclass
class Http2Connection:
    """Streams share one connection: many independent stream states, one dict of them."""

    streams: dict[int, StreamState] = field(default_factory=dict)
    received: dict[int, int] = field(default_factory=dict)


def on_frame(conn: Http2Connection, frame: Frame) -> FrameOutcome:
    """One connection, many stream states: each frame advances only its own stream's state."""
    state = conn.streams.get(frame.stream_id, StreamState.IDLE)

    if state is StreamState.CLOSED:
        return FrameOutcome.ERROR_FRAME_AFTER_CLOSED

    if state is StreamState.IDLE:
        if frame.frame_type != "HEADERS":
            # DATA cannot open a stream: only HEADERS may.
            return FrameOutcome.ERROR_DATA_ON_IDLE_STREAM

        conn.received[frame.stream_id] = frame.payload_len
        if frame.end_stream:
            conn.streams[frame.stream_id] = StreamState.HALF_CLOSED_REMOTE
            return FrameOutcome.STREAM_HALF_CLOSED

        conn.streams[frame.stream_id] = StreamState.OPEN
        return FrameOutcome.STREAM_OPENED

    if state is StreamState.OPEN:
        conn.received[frame.stream_id] = conn.received.get(frame.stream_id, 0) + frame.payload_len
        if frame.end_stream:
            conn.streams[frame.stream_id] = StreamState.HALF_CLOSED_REMOTE
            return FrameOutcome.STREAM_HALF_CLOSED
        return FrameOutcome.ACCEPTED

    # HALF_CLOSED_REMOTE: the peer already signalled end_stream, so any further frame
    # from them closes the stream outright rather than being accepted as more data.
    conn.streams[frame.stream_id] = StreamState.CLOSED
    return FrameOutcome.STREAM_CLOSED


if __name__ == "__main__":
    conn = Http2Connection()

    data_on_idle = on_frame(conn, Frame(stream_id=1, frame_type="DATA", payload_len=10, end_stream=False))
    assert data_on_idle is FrameOutcome.ERROR_DATA_ON_IDLE_STREAM
    assert conn.streams.get(1, StreamState.IDLE) is StreamState.IDLE

    opened = on_frame(conn, Frame(stream_id=1, frame_type="HEADERS", payload_len=20, end_stream=False))
    assert opened is FrameOutcome.STREAM_OPENED
    assert conn.streams[1] is StreamState.OPEN

    # Interleave a second stream while the first is mid-flight: each stream advances alone.
    on_frame(conn, Frame(stream_id=3, frame_type="HEADERS", payload_len=5, end_stream=True))
    assert conn.streams[3] is StreamState.HALF_CLOSED_REMOTE
    assert conn.streams[1] is StreamState.OPEN

    half_closed = on_frame(conn, Frame(stream_id=1, frame_type="DATA", payload_len=30, end_stream=True))
    assert half_closed is FrameOutcome.STREAM_HALF_CLOSED
    assert conn.received[1] == 50

    closed = on_frame(conn, Frame(stream_id=1, frame_type="DATA", payload_len=1, end_stream=False))
    assert closed is FrameOutcome.STREAM_CLOSED

    after_closed = on_frame(conn, Frame(stream_id=1, frame_type="DATA", payload_len=1, end_stream=False))
    assert after_closed is FrameOutcome.ERROR_FRAME_AFTER_CLOSED

    print("[OK] h2_streams.py")
