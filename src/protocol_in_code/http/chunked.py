from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ChunkParserState(str, Enum):
    SIZE_LINE = "SizeLine"
    DATA = "Data"
    DATA_CRLF = "DataCrlf"
    DONE = "Done"
    ERROR = "Error"


@dataclass
class ChunkParser:
    """Chunked is a parser state machine: the state field is the whole story."""

    state: ChunkParserState = ChunkParserState.SIZE_LINE
    bytes_needed: int = 0
    chunks: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ParsedBody:
    ok: bool
    body: str


def feed_line(parser: ChunkParser, line: str) -> None:
    """A 'line' is a size-line or the CRLF that trails a chunk's data; DONE and ERROR ignore input."""
    if parser.state is ChunkParserState.SIZE_LINE:
        try:
            size = int(line.strip(), 16)
        except ValueError:
            parser.state = ChunkParserState.ERROR
            return

        if size == 0:
            parser.state = ChunkParserState.DONE
            return

        parser.bytes_needed = size
        parser.state = ChunkParserState.DATA

    elif parser.state is ChunkParserState.DATA_CRLF:
        if line != "":
            parser.state = ChunkParserState.ERROR
            return
        parser.state = ChunkParserState.SIZE_LINE

    else:
        parser.state = ChunkParserState.ERROR


def feed_data(parser: ChunkParser, data: str) -> None:
    """Data is only accepted in the DATA state, and must satisfy exactly bytes_needed."""
    if parser.state is not ChunkParserState.DATA:
        parser.state = ChunkParserState.ERROR
        return

    if len(data) != parser.bytes_needed:
        parser.state = ChunkParserState.ERROR
        return

    parser.chunks.append(data)
    parser.state = ChunkParserState.DATA_CRLF


def parse_chunked(lines: list[str]) -> ParsedBody:
    """Convenience wrapper: drive the state machine across a full message, size/data/CRLF/..."""
    parser = ChunkParser()
    index = 0

    while parser.state not in (ChunkParserState.DONE, ChunkParserState.ERROR):
        if index >= len(lines):
            parser.state = ChunkParserState.ERROR
            break

        if parser.state is ChunkParserState.DATA:
            feed_data(parser, lines[index])
        else:
            feed_line(parser, lines[index])
        index += 1

    if parser.state is not ChunkParserState.DONE:
        return ParsedBody(ok=False, body="")

    return ParsedBody(ok=True, body="".join(parser.chunks))


if __name__ == "__main__":
    parser = ChunkParser()
    feed_line(parser, "5")
    assert parser.state is ChunkParserState.DATA
    feed_data(parser, "hello")
    assert parser.state is ChunkParserState.DATA_CRLF
    feed_line(parser, "")
    assert parser.state is ChunkParserState.SIZE_LINE
    feed_line(parser, "0")
    assert parser.state is ChunkParserState.DONE

    result = parse_chunked(["5", "hello", "", "6", " world", "", "0"])
    assert result.ok
    assert result.body == "hello world"

    bad = ChunkParser()
    feed_line(bad, "not-hex")
    assert bad.state is ChunkParserState.ERROR

    wrong_length = ChunkParser()
    feed_line(wrong_length, "5")
    feed_data(wrong_length, "toolong")
    assert wrong_length.state is ChunkParserState.ERROR

    print("[OK] chunked.py")
