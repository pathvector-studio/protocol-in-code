# Session 01 / Module 01: STUN Tells You Your Own Address

## Position

- Track: ICE
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/ice/module-01/index.html`
- Source file: `src/protocol_in_code/ice/stun.py`
- Walkthrough script: `examples/ice/session_01_walkthrough.py`

## Core Question

What does a STUN server actually tell you, and how do you turn that answer into knowledge that you are behind a NAT?

## Outcome

By the end of this session, the learner should be able to:

- state the one thing a STUN server does, in one sentence
- explain what `nat_mapping=None` means and why it is the identity function
- explain why `behind_nat()` is a single tuple comparison, not a protocol
- explain why STUN alone cannot tell a client whether a NAT is in the path — only the comparison can

## Read Order

1. Read the module comment at the top of the file
2. Read `BindingRequest`
3. Read `BindingResponse`
4. Read `stun_query()`
5. Read `behind_nat()`
6. Run `examples/ice/session_01_walkthrough.py`

## Read It Like Code

```python
stun_query(
    local_ip,
    local_port,
    nat_mapping,
    server,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `from_ip` / `from_port` (`BindingRequest`) | The client's own claim about itself. The server does not need to believe it — it is only ever the starting point for comparison. |
| `mapped_ip` / `mapped_port` (`BindingResponse`) | Not an echo of the request. It is the return address the server actually observed on the packet's envelope. |
| `nat_mapping` (`stun_query`) | A callable standing in for whatever sits on the path. `None` means nothing rewrites the envelope; passing a function means something does. |

## Decision Flow

```text
nat_mapping is None       -> seen_ip, seen_port = local_ip, local_port   (identity)
nat_mapping is a function  -> seen_ip, seen_port = nat_mapping(local_ip, local_port, server)
mapped != local             -> behind_nat() is True
mapped == local              -> behind_nat() is False
```

## Reading Lens

The important move in this session is to stop thinking of STUN as "a protocol that detects NATs" and start asking:

- what did the server actually see arrive, versus what the client believes it sent?
- is `nat_mapping` standing in for "no NAT" or "some NAT," and how does the function's return value encode that?
- where does the comparison happen — inside `stun_query()`, or somewhere else?

## Toy Model Boundary

Real STUN (RFC 5389 / RFC 8489) carries a transaction ID, message integrity via a message-integrity attribute, and a XOR-MAPPED-ADDRESS attribute so the mapped address survives NATs that rewrite payloads that look like addresses. This lesson keeps `BindingRequest` and `BindingResponse` to the two fields that carry the actual discovery — the address and port — so the one fact that matters (the server reports what it saw, not what you claimed) stays the whole story.

`nat_mapping` is a plain `Callable`, not a simulated network stack. It exists so the walkthrough can express "no NAT" and "some NAT" as two different arguments to the same function, without building a real UDP path.

## Code Landmarks

### Module comment

The file opens with the thesis of the whole track: a STUN server reads the envelope of the packet that arrived and reports the source address and port it saw — never the payload's claimed origin. `nat_behavior.py` and `candidates.py` both build on this one fact.

### `stun_query()`

The main reading target. When `nat_mapping is None`, `seen_ip, seen_port` are set directly from the request — this is the identity function, spelled out in code rather than left implicit. When `nat_mapping` is a callable, it is handed the request's claimed address plus the server, and whatever it returns becomes the response. `stun_query()` never compares anything; it only reports.

### `behind_nat()`

One line: a tuple inequality. `(response.mapped_ip, response.mapped_port) != local`. This is the headline of the session — the discovery IS the comparison. Nothing about `stun_query()` or `BindingResponse` "detects" a NAT; detection is this one equality check living in the caller.

## Failure Questions

Use the source file to answer these:

1. What does it mean, in code, for `nat_mapping` to be `None`? Which two variables get set, and from what?
2. If `nat_mapping` is a function that always returns the same `(ip, port)` regardless of its arguments, does `stun_query()` care? Why not?
3. `behind_nat()` takes `local` as a tuple, not as two separate arguments. Why does that matter for how the comparison is written?
4. Can `stun_query()` alone — without `behind_nat()` — ever tell you whether you are behind a NAT? What is missing?
5. Why does `BindingResponse` not include a copy of `BindingRequest`? What would comparing them accomplish that `behind_nat()` does not already do with `local`?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/ice/session_01_walkthrough.py
```

The walkthrough queries with no NAT (response echoes local, `behind_nat` is `False`), then with a NAT mapping in the path (response differs, `behind_nat` is `True`), and shows that the response carries exactly what the server saw — the same local address through the same NAT always maps to the same observed address.

## Done When

The learner can say all of the following without looking at notes:

- "A STUN server does one thing: it tells you the return address it saw on your packet."
- "`nat_mapping=None` is not a special case — it is the identity function, spelled out."
- "You don't detect a NAT by asking STUN a question with a yes/no answer; you detect it by comparing the response to what you already knew about yourself."

## References

- RFC 5389 (Session Traversal Utilities for NAT — STUN)
- RFC 8489 (STUN, obsoletes RFC 5389)
