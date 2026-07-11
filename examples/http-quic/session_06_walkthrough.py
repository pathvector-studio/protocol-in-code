from protocol_in_code.http.chunked import ChunkParser, ChunkParserState, feed_data, feed_line, parse_chunked


def main() -> None:
    print("Session 06 walkthrough: Chunked is a parser state machine")
    print()

    parser = ChunkParser()

    feed_line(parser, "5")
    marker = "OK" if parser.state is ChunkParserState.DATA else "NG"
    print(f"[{marker}] size line '5'              -> state={parser.state.value}")

    feed_data(parser, "hello")
    marker = "OK" if parser.state is ChunkParserState.DATA_CRLF else "NG"
    print(f"[{marker}] 5 bytes fed                -> state={parser.state.value}")

    feed_line(parser, "")
    marker = "OK" if parser.state is ChunkParserState.SIZE_LINE else "NG"
    print(f"[{marker}] trailing CRLF consumed     -> state={parser.state.value}")

    feed_line(parser, "0")
    marker = "OK" if parser.state is ChunkParserState.DONE else "NG"
    print(f"[{marker}] size 0 terminates          -> state={parser.state.value}")

    result = parse_chunked(["5", "hello", "", "6", " world", "", "0"])
    marker = "OK" if result.ok and result.body == "hello world" else "NG"
    print(f"[{marker}] two chunks assembled       -> body={result.body!r}")

    bad_hex = ChunkParser()
    feed_line(bad_hex, "not-hex")
    marker = "OK" if bad_hex.state is ChunkParserState.ERROR else "NG"
    print(f"[{marker}] non-hex size line          -> state={bad_hex.state.value}")

    after_done = ChunkParser()
    feed_line(after_done, "0")
    feed_line(after_done, "anything")
    marker = "OK" if after_done.state is ChunkParserState.ERROR else "NG"
    print(f"[{marker}] feed after DONE is sticky  -> state={after_done.state.value}")

    wrong_length = ChunkParser()
    feed_line(wrong_length, "5")
    feed_data(wrong_length, "toolong")
    marker = "OK" if wrong_length.state is ChunkParserState.ERROR else "NG"
    print(f"[{marker}] data length mismatch       -> state={wrong_length.state.value}")


if __name__ == "__main__":
    main()
