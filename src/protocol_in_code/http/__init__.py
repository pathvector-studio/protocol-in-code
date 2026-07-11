"""HTTP reading examples for the Protocol in Code course."""

from .caching import (
    CachedResponse,
    ResponseDirectives,
    RevalidationResult,
    ReuseDecision,
    StoreDecision,
    can_reuse,
    can_store,
    revalidate,
)
from .chunked import ChunkParser, ChunkParserState, ParsedBody, feed_data, feed_line, parse_chunked
from .h2_streams import Frame, FrameOutcome, Http2Connection, StreamState
from .h2_streams import on_frame as h2_on_frame
from .headers import RULES, HeaderIssue, HeaderProblem, check_headers
from .headers import normalize_name as normalize_header_name
from .parse import ParseOutcome, ParseResult, Request, parse_request
from .pool import CheckoutOutcome, CheckoutResult, ConnectionPool, IdleConnection, checkin, checkout
from .redirect import MAX_REDIRECTS, RedirectOutcome, RedirectResult, follow_redirects
from .server_loop import Response, ToyHttpServer, handle_connection

__all__ = [
    "MAX_REDIRECTS",
    "RULES",
    "CachedResponse",
    "CheckoutOutcome",
    "CheckoutResult",
    "ChunkParser",
    "ChunkParserState",
    "ConnectionPool",
    "Frame",
    "FrameOutcome",
    "HeaderIssue",
    "HeaderProblem",
    "Http2Connection",
    "IdleConnection",
    "ParseOutcome",
    "ParseResult",
    "ParsedBody",
    "RedirectOutcome",
    "RedirectResult",
    "Request",
    "Response",
    "ResponseDirectives",
    "RevalidationResult",
    "ReuseDecision",
    "StoreDecision",
    "StreamState",
    "ToyHttpServer",
    "can_reuse",
    "can_store",
    "check_headers",
    "checkin",
    "checkout",
    "feed_data",
    "feed_line",
    "follow_redirects",
    "h2_on_frame",
    "handle_connection",
    "normalize_header_name",
    "parse_chunked",
    "parse_request",
    "revalidate",
]
