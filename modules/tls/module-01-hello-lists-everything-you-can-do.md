# Session 01 / Module 01: Hello Lists Everything You Can Do

## Position

- Track: TLS
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/tls/module-01/index.html`
- Source file: `src/protocol_in_code/tls/messages.py`
- Walkthrough script: `examples/tls/session_01_walkthrough.py`

## Core Question

What is a TLS ClientHello actually made of, and what makes one invalid before any negotiation starts?

## Outcome

By the end of this session, the learner should be able to:

- name the two required fields of a `ClientHello` and the three that carry defaults
- explain why `alpn` and `session_ticket` are optional but `offered_versions`, `cipher_suites`, and `server_name` are not
- list, in order, the three ways `validate_client_hello()` can reject a hello
- explain why a `ServerHello` is described as "one pick," not a new declaration

## Read Order

1. Read `HelloValidity`
2. Read `ClientHello`
3. Read `ServerHello`
4. Read `validate_client_hello()`
5. Run `examples/tls/session_01_walkthrough.py`
6. Explain each early return in your own words

## Read It Like Code

```python
ClientHello(
    offered_versions,
    cipher_suites,
    server_name,
    alpn=(),
    session_ticket=None,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `offered_versions` | The client's ordered menu of protocol versions it can speak. Empty means nothing to negotiate. |
| `cipher_suites` | The client's ordered menu of cryptographic algorithm sets. Empty means nothing to negotiate. |
| `server_name` | The SNI hostname the client is asking for. Empty is treated as no name was declared. |
| `alpn` | Application-layer protocols (e.g. `h2`, `http/1.1`). Defaults to an empty tuple - offering none is legal. |
| `session_ticket` | Opaque resumption material from a prior session. Defaults to `None` - most first connections have none. |

## Decision Flow

```text
offered_versions empty   -> NoVersions
cipher_suites empty      -> NoCipherSuites
server_name == ""        -> EmptyServerName
otherwise                -> Valid
```

## Reading Lens

The important move in this session is to stop thinking of a ClientHello as a network packet and start asking:

- what does this object claim the client can do?
- which fields are required declarations versus optional extras?
- which single early return explains why this hello was rejected?

## Toy Model Boundary

Real TLS ClientHellos are binary-encoded, carry a random nonce, a session ID, compression methods, and a long list of extensions (key_share, supported_groups, signature_algorithms, and more). This lesson keeps `ClientHello` as a plain frozen dataclass with five fields because the reading target is "what does a hello declare and when is it invalid," not wire encoding.

`ServerHello` here is likewise a minimal frozen dataclass - three fields, no extensions, no random, no binder. It exists in this module only to make the point that a server's answer is a *pick from* the client's declared lists, which Session 02 makes precise.

## Code Landmarks

### `HelloValidity`

A `str` `Enum` with four members. Note it is not a boolean - "invalid" has three distinct flavors, and the flavor is the useful signal.

### `ClientHello`

Frozen, so an instance can never be mutated after construction - a hello is a fixed declaration, not something negotiation edits in place. `alpn` and `session_ticket` are the only two fields with defaults; everything else must be supplied.

### `ServerHello`

Also frozen. Its docstring is the thesis for the whole session: the reply is not a new declaration, it is one pick from the client's list. Session 02 is where that pick is actually computed.

### `validate_client_hello()`

The main reading target. Three `if` checks, each an early return, checked in a fixed order: versions, then suites, then server name. A hello that fails more than one check still only reports the first failure it hits.

## Failure Questions

Use the source file to answer these:

1. A `ClientHello` has empty `offered_versions` AND empty `cipher_suites`. Which `HelloValidity` comes back, and why does the other failure never get reported?
2. What is the exact value of `hello.alpn` if you construct a `ClientHello` supplying only `offered_versions`, `cipher_suites`, and `server_name`?
3. Is `session_ticket=""` (empty string) treated the same as `session_ticket=None` by `validate_client_hello()`? Check what the function actually inspects.
4. Why can `ClientHello` instances be used as dictionary keys or placed in a set, and what property of the class makes this possible?
5. `ServerHello.chosen_alpn` defaults to `None`. Given only `messages.py`, what does that default tell you about whether ALPN negotiation is mandatory?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/tls/session_01_walkthrough.py
```

The walkthrough builds a fully populated hello and prints its fields, confirms the two optional fields' defaults, and drives each invalid-hello case to its exact `HelloValidity` member.

## Done When

The learner can say all of the following without looking at notes:

- "A ClientHello is a plain, printable declaration of five fields - three required, two defaulted."
- "Invalid is not one outcome, it is one of three named reasons, checked in a fixed order."
- "A ServerHello does not invent anything; every field it can choose comes from what the client already declared."

## References

- RFC 8446 Section 4.1.2 (Client Hello)
- RFC 7301 (Application-Layer Protocol Negotiation Extension)
