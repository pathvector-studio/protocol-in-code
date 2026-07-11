from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

MAX_REDIRECTS = 5


class RedirectOutcome(str, Enum):
    RESOLVED = "Resolved"
    TOO_MANY_REDIRECTS = "TooManyRedirects"
    REDIRECT_LOOP = "RedirectLoop"
    DEAD_END = "DeadEnd"


@dataclass(frozen=True)
class RedirectResult:
    outcome: RedirectOutcome
    final_url: str | None
    final_method: str
    hops: tuple[str, ...]


def _rewrite_method(status: int, method: str) -> str:
    """303 always becomes GET; 307/308 preserve the method; 301/302 rewrite POST (historical
    behavior from early browsers, kept by convention rather than by the original RFC text)."""
    if status == 303:
        return "GET"
    if status in (307, 308):
        return method
    if status in (301, 302) and method == "POST":
        return "GET"
    return method


def follow_redirects(
    start_url: str,
    method: str,
    responses: dict[str, tuple[int, str | None]],
) -> RedirectResult:
    """Redirects are a bounded loop: a visited set catches cycles, a counter catches chains."""
    visited: set[str] = set()
    hops: list[str] = []
    url = start_url
    current_method = method

    for _ in range(MAX_REDIRECTS + 1):
        if url in visited:
            return RedirectResult(RedirectOutcome.REDIRECT_LOOP, None, current_method, tuple(hops))
        visited.add(url)
        hops.append(url)

        response = responses.get(url)
        if response is None:
            return RedirectResult(RedirectOutcome.DEAD_END, None, current_method, tuple(hops))

        status, location = response
        if status < 300 or status >= 400:
            return RedirectResult(RedirectOutcome.RESOLVED, url, current_method, tuple(hops))

        if location is None:
            return RedirectResult(RedirectOutcome.DEAD_END, None, current_method, tuple(hops))

        current_method = _rewrite_method(status, current_method)
        url = location

    return RedirectResult(RedirectOutcome.TOO_MANY_REDIRECTS, None, current_method, tuple(hops))


if __name__ == "__main__":
    linear = {
        "/a": (301, "/b"),
        "/b": (200, None),
    }
    result = follow_redirects("/a", "GET", linear)
    assert result.outcome is RedirectOutcome.RESOLVED
    assert result.final_url == "/b"
    assert result.hops == ("/a", "/b")

    loop = {
        "/a": (302, "/b"),
        "/b": (302, "/a"),
    }
    result = follow_redirects("/a", "GET", loop)
    assert result.outcome is RedirectOutcome.REDIRECT_LOOP

    chain = {f"/{i}": (302, f"/{i + 1}") for i in range(MAX_REDIRECTS + 2)}
    result = follow_redirects("/0", "GET", chain)
    assert result.outcome is RedirectOutcome.TOO_MANY_REDIRECTS

    dead_end = {"/a": (302, "/missing")}
    result = follow_redirects("/a", "GET", dead_end)
    assert result.outcome is RedirectOutcome.DEAD_END

    post_303 = {"/a": (303, "/b"), "/b": (200, None)}
    result = follow_redirects("/a", "POST", post_303)
    assert result.final_method == "GET"

    post_307 = {"/a": (307, "/b"), "/b": (200, None)}
    result = follow_redirects("/a", "POST", post_307)
    assert result.final_method == "POST"

    post_302 = {"/a": (302, "/b"), "/b": (200, None)}
    result = follow_redirects("/a", "POST", post_302)
    assert result.final_method == "GET"

    print("[OK] redirect.py")
