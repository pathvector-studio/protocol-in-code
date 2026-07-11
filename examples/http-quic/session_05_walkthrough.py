from protocol_in_code.http.redirect import MAX_REDIRECTS, RedirectOutcome, follow_redirects


def main() -> None:
    print("Session 05 walkthrough: Redirects are a bounded loop")
    print()

    two_hop = {
        "/a": (301, "/b"),
        "/b": (200, None),
    }
    result = follow_redirects("/a", "GET", two_hop)
    marker = "OK" if result.outcome is RedirectOutcome.RESOLVED and result.hops == ("/a", "/b") else "NG"
    print(f"[{marker}] 2-hop chain resolves      -> {result.outcome.value} hops={result.hops}")

    post_303 = {"/a": (303, "/b"), "/b": (200, None)}
    result = follow_redirects("/a", "POST", post_303)
    marker = "OK" if result.outcome is RedirectOutcome.RESOLVED and result.final_method == "GET" else "NG"
    print(f"[{marker}] 303 rewrites POST to GET  -> method={result.final_method}")

    post_307 = {"/a": (307, "/b"), "/b": (200, None)}
    result = follow_redirects("/a", "POST", post_307)
    marker = "OK" if result.outcome is RedirectOutcome.RESOLVED and result.final_method == "POST" else "NG"
    print(f"[{marker}] 307 preserves POST        -> method={result.final_method}")

    post_302 = {"/a": (302, "/b"), "/b": (200, None)}
    result = follow_redirects("/a", "POST", post_302)
    marker = "OK" if result.outcome is RedirectOutcome.RESOLVED and result.final_method == "GET" else "NG"
    print(f"[{marker}] 302 rewrites POST to GET  -> method={result.final_method}")

    self_loop = {"/a": (302, "/a")}
    result = follow_redirects("/a", "GET", self_loop)
    marker = "OK" if result.outcome is RedirectOutcome.REDIRECT_LOOP else "NG"
    print(f"[{marker}] self-loop is caught       -> {result.outcome.value}")

    deep_chain = {f"/{i}": (302, f"/{i + 1}") for i in range(MAX_REDIRECTS + 2)}
    result = follow_redirects("/0", "GET", deep_chain)
    marker = "OK" if result.outcome is RedirectOutcome.TOO_MANY_REDIRECTS else "NG"
    print(f"[{marker}] 6-deep chain trips limit   -> {result.outcome.value} hops={len(result.hops)}")

    missing_target = {"/a": (302, "/nowhere")}
    result = follow_redirects("/a", "GET", missing_target)
    marker = "OK" if result.outcome is RedirectOutcome.DEAD_END else "NG"
    print(f"[{marker}] Location points nowhere    -> {result.outcome.value}")


if __name__ == "__main__":
    main()
