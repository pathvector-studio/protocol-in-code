# Session 01 / Module 01: Discovery Is Shouting into the Dark

## Position

- Track: DHCP
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/dhcp/module-01/index.html`
- Source file: `src/protocol_in_code/dhcp/discover.py`
- Walkthrough script: `examples/dhcp/session_01_walkthrough.py`

## Core Question

A DHCP client has no IP address yet. How does a message even get sent, and what does that fact do to the shape of the message itself?

## Outcome

By the end of this session, the learner should be able to:

- explain why `DhcpMessage` has no destination field, structurally, not just by convention
- name the five message types and the one field each type leans on
- explain what `validate_message()` checks and why it only checks presence, not correctness
- say why DISCOVER is the one message type that needs almost nothing filled in

## Read Order

1. Read `MessageType`
2. Read `MessageValidity`
3. Read `DhcpMessage`
4. Read `make_discover()`
5. Read `validate_message()`
6. Run `examples/dhcp/session_01_walkthrough.py`

## Read It Like Code

```python
DhcpMessage(
    message_type,
    transaction_id,
    client_mac,
    offered_ip=None,
    server_id=None,
    requested_ip=None,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `message_type` | Picks which of the optional fields below `validate_message()` will demand. |
| `transaction_id` | The only thing that ties a client's DISCOVER to the OFFERs, REQUEST, and ACK that answer it. |
| `client_mac` | The client's one stable identity before it has an IP. Everything else in DORA hangs off this. |
| `offered_ip` | Set by a server in an OFFER (or ACK); absent on DISCOVER because no server has proposed anything yet. |
| `server_id` | Set by a server in an OFFER; echoed back by the client in REQUEST so the right server knows it won. |
| `requested_ip` | Set by the client in REQUEST, echoing the `offered_ip` it is accepting. |

## Decision Flow

```text
msg.message_type is OFFER   and offered_ip is None  -> MISSING_OFFERED_IP
msg.message_type is REQUEST and server_id is None    -> MISSING_SERVER_ID
msg.message_type is ACK     and offered_ip is None   -> MISSING_OFFERED_IP
otherwise                                             -> VALID
```

## Reading Lens

The temptation with this file is to skim `DhcpMessage` as "just a struct with some optional fields" and move on. Resist that. The important move in this session is to stop looking for a destination field and start asking:

- if this message has no destination, who is expected to pick it up?
- which fields does `make_discover()` bother to fill, and which does it leave at their defaults?
- what does `validate_message()` refuse to say anything about? (Hint: it never touches `client_mac` or `transaction_id`.)

## Toy Model Boundary

Real DHCP messages carry a magic cookie, an options list (including the actual message-type option, which real implementations encode as option 53 rather than a dataclass field), a `giaddr` for relay agents crossing subnet boundaries, and BOOTP-legacy fields like `ciaddr`/`yiaddr`/`siaddr`. This toy collapses all of that into one flat, frozen dataclass with six fields, and it has no concept of a relay agent at all — every message here is imagined as happening on one broadcast segment. What survives the simplification is the one structural fact this session is built around: absence of a destination is what "broadcast" means here, not a special-cased address like `255.255.255.255`.

## Code Landmarks

### `DhcpMessage`

Frozen, six fields, three of them defaulted to `None`. There is no `dest`, no `destination`, no `broadcast: bool` — nothing that names where the packet goes. That is not an omission the lesson works around; it is the thing the lesson is about.

### `make_discover()`

Fills exactly three fields: `message_type`, `transaction_id`, `client_mac`. Everything else — `offered_ip`, `server_id`, `requested_ip` — stays `None`, because a client that has never heard from a server has nothing to put there. Read the docstring closely: it states outright that the missing destination is on purpose, because the client "doesn't know a server's address yet, so it can't address one."

### `validate_message()`

Three `if` statements, each gated on `message_type`. It is a presence check, not a correctness check — it will happily call an OFFER with `offered_ip="not-an-ip"` valid. It also says nothing at all about DISCOVER: a DISCOVER with `message_type=MessageType.DISCOVER` and nothing else set falls through every branch to `VALID`, because DISCOVER makes no promises about `offered_ip`, `server_id`, or `requested_ip` in the first place.

## Failure Questions

Use the source file to answer these:

1. `DhcpMessage` has fields for `offered_ip`, `server_id`, and `requested_ip`, but nothing for where the packet goes. What does the absence of that field mean about how this message reaches the network?
2. `make_discover()`'s docstring gives a reason for the missing destination. What is a DISCOVER client missing that a server or an already-configured client has?
3. `validate_message()` checks OFFER and ACK for the same missing field. Which field, and what do those two message types have in common that REQUEST does not?
4. Why does `validate_message()` check REQUEST for `server_id` but not for `requested_ip`, even though `accept_offer()` (Session 02) always sets both together?
5. If you built a `DhcpMessage` with `message_type=MessageType.DISCOVER` and `offered_ip="192.0.2.10"` set, what would `validate_message()` return? What does that tell you about what this function does and does not enforce?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dhcp/session_01_walkthrough.py
```

The walkthrough builds a DISCOVER and inspects its dataclass fields directly to prove no destination field exists anywhere on the type, then runs OFFER and REQUEST messages through `validate_message()` in both their valid and field-missing forms.

## Done When

The learner can say all of the following without looking at notes:

- "DISCOVER has no destination field because the client has no address to send from and no server address to send to — broadcast isn't a value here, it's the absence of a value."
- "`validate_message()` only checks that a message type's required fields are present, not that their contents make sense."
- "OFFER and ACK both require `offered_ip`; REQUEST requires `server_id` instead, because REQUEST is about naming which offer the client picked."

## References

- RFC 2131 Section 3.1 — the DORA message exchange this file's five `MessageType` values walk through
