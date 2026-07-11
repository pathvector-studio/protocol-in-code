from protocol_in_code.http.h2_streams import Frame, FrameOutcome, Http2Connection, StreamState, on_frame


def main() -> None:
    print("Session 07 walkthrough: Streams share one connection")
    print()

    conn = Http2Connection()

    data_on_idle = on_frame(conn, Frame(stream_id=1, frame_type="DATA", payload_len=10, end_stream=False))
    marker = "OK" if data_on_idle is FrameOutcome.ERROR_DATA_ON_IDLE_STREAM else "NG"
    print(f"[{marker}] DATA on idle stream 1      -> {data_on_idle.value}")

    opened = on_frame(conn, Frame(stream_id=1, frame_type="HEADERS", payload_len=20, end_stream=False))
    marker = "OK" if opened is FrameOutcome.STREAM_OPENED and conn.streams[1] is StreamState.OPEN else "NG"
    print(f"[{marker}] HEADERS opens stream 1     -> {opened.value} state={conn.streams[1].value}")

    on_frame(conn, Frame(stream_id=3, frame_type="HEADERS", payload_len=5, end_stream=True))
    marker = "OK" if conn.streams[3] is StreamState.HALF_CLOSED_REMOTE and conn.streams[1] is StreamState.OPEN else "NG"
    print(f"[{marker}] stream 3 interleaved       -> stream3={conn.streams[3].value} stream1={conn.streams[1].value}")

    half_closed = on_frame(conn, Frame(stream_id=1, frame_type="DATA", payload_len=30, end_stream=True))
    marker = "OK" if half_closed is FrameOutcome.STREAM_HALF_CLOSED and conn.received[1] == 50 else "NG"
    print(f"[{marker}] end_stream DATA on 1       -> {half_closed.value} received={conn.received[1]}")

    closed = on_frame(conn, Frame(stream_id=1, frame_type="DATA", payload_len=1, end_stream=False))
    marker = "OK" if closed is FrameOutcome.STREAM_CLOSED and conn.streams[1] is StreamState.CLOSED else "NG"
    print(f"[{marker}] any frame after half-close -> {closed.value} state={conn.streams[1].value}")

    after_closed = on_frame(conn, Frame(stream_id=1, frame_type="DATA", payload_len=1, end_stream=False))
    marker = "OK" if after_closed is FrameOutcome.ERROR_FRAME_AFTER_CLOSED else "NG"
    print(f"[{marker}] frame after CLOSED         -> {after_closed.value}")


if __name__ == "__main__":
    main()
