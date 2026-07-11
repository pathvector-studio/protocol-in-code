# Session 03 / Module 03: Anyone Can Answer

## Position

- Track: ARP/ND
- Session: 03
- Site lesson: `pathvector-site/courses/protocols-in-code/arp/module-03/index.html`
- Source file: `src/protocol_in_code/arp/gratuitous.py`
- Walkthrough script: `examples/arp/session_03_walkthrough.py`

## Core Question

ARP has no authentication — so when an unsolicited announcement shows up claiming an IP-to-MAC mapping, what decides whether the cache believes it?

## Outcome

By the end of this session, the learner should be able to:

- name the four `ProcessOutcome` values and which situation produces each one
- explain what makes an announcement "unsolicited" versus a reply to something we asked
- describe exactly what `ACCEPT_ALL` lets an attacker do to a cache entry that was already trusted
- explain what `ONLY_IF_KNOWN` refuses, what it still allows, and why it is not equivalent to real Dynamic ARP Inspection

## Read Order

1. Read the module comment at the top of the file
2. Read `AcceptPolicy`
3. Read `ProcessOutcome`
4. Read `ArpAnnouncement`
5. Read `process_announcement()`
6. Run `examples/arp/session_03_walkthrough.py`

## Read It Like Code

```python
ArpAnnouncement(
    ip,
    mac,
    is_reply_to_us,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `ip` | The address the announcement claims to speak for. |
| `mac` | The hardware address the announcement claims maps to that IP. Nothing forces this to be true. |
| `is_reply_to_us` | The one signal `process_announcement()` has for "we asked for this." Everything else is unsolicited. |

## Decision Flow

```text
no existing entry for this IP
  -> confirm the mapping                              -> CREATED

existing entry, and (is_reply_to_us OR existing.state is INCOMPLETE)
  -> confirm the mapping
     existing.mac == announcement.mac -> CONFIRMED
     otherwise                        -> OVERWROTE

existing entry, unsolicited, and NOT INCOMPLETE
  policy is ONLY_IF_KNOWN -> REFUSED_UNSOLICITED   (mapping untouched)
  policy is ACCEPT_ALL    -> confirm the mapping
     existing.mac == announcement.mac -> CONFIRMED
     otherwise                        -> OVERWROTE
```

## Reading Lens

The important move in this session is to stop treating "an ARP reply arrived" as automatically trustworthy and start asking:

- did we solicit this, or did it just show up?
- was there already a mapping here that this announcement is changing?
- under the policy in force, was this announcement allowed to change it — and what did it change it to?

Read this against Session 01's `lookup()`: that function only ever *degrades* trust (`REACHABLE -> STALE`) as a side effect of time passing. `process_announcement()` is the only place in this track's source that can *upgrade* an entry straight back to full trust — `REACHABLE`, freshly timestamped — on the word of a message that, under `ACCEPT_ALL`, nobody had to prove.

## Toy Model Boundary

This is not real Dynamic ARP Inspection. Real DAI validates announcements against a trusted binding table, typically built from DHCP snooping records, so a switch can check a claimed IP-to-MAC pair against a binding it independently trusts before allowing it onto the wire. `ONLY_IF_KNOWN` has no such binding table — it has exactly one rule: refuse an unsolicited announcement that would overwrite a mapping already in the cache. It still lets a gratuitous announcement create a brand-new entry (`existing is None -> CREATED`, unconditionally, regardless of policy) and still lets an in-flight resolution (`existing.state is NeighborState.INCOMPLETE`) be completed by an unsolicited reply. Both of those are places a real attacker can still plant a false mapping under `ONLY_IF_KNOWN` — this toy only closes the "overwrite something already trusted" door, not the "walk in the door while it's still open" one. There's also no rate limiting, no logging, and no notion of which interface or VLAN an announcement arrived on.

## Code Landmarks

### The module comment

States the thesis and the defense in the same breath: ARP has no authentication, so `ACCEPT_ALL` is the spoofing surface and `ONLY_IF_KNOWN` is "a mitigation, not a fix."

### `process_announcement()`

The main reading target, and the whole file's only function. Read the four branches top to bottom — notice the policy check (`if policy is AcceptPolicy.ONLY_IF_KNOWN`) only appears in the *third* branch. The first two branches (`existing is None`, and `is_reply_to_us or existing.state is NeighborState.INCOMPLETE`) both confirm unconditionally, no matter what `policy` is.

### The `CONFIRMED` vs `OVERWROTE` split

Both come from the same code path: `confirm()` runs first, then `existing.mac == announcement.mac` decides the label. This comparison uses the *pre-confirm* `existing.mac` — captured before `confirm()` overwrites the entry — against the newly announced one. Note that an `INCOMPLETE` entry's `mac` is `None`, so this comparison can never be true for a resolution still in flight; completing an `INCOMPLETE` entry always reports `OVERWROTE`, even though nothing was actually being lied about — it's `None` becoming a real MAC, not one MAC replacing another.

## Failure Questions

Use the source file to answer these:

1. Under `AcceptPolicy.ACCEPT_ALL`, what outcome does an unsolicited announcement (`is_reply_to_us=False`) produce when it targets an IP whose cache entry is already `REACHABLE` with a *different* MAC?
2. Under `AcceptPolicy.ONLY_IF_KNOWN`, does the same announcement in question 1 change the cached MAC at all? What outcome value is returned instead?
3. Which specific condition in `process_announcement()` lets a gratuitous announcement populate a cache entry that didn't exist before, and does the active `policy` affect that branch at all?
4. If `existing.state is NeighborState.INCOMPLETE` and an unsolicited announcement arrives with a real MAC, what `ProcessOutcome` comes back, and why is it not `CONFIRMED`?
5. What has to be true about both `is_reply_to_us` and `existing.mac` for `process_announcement()` to return `ProcessOutcome.CONFIRMED`?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/arp/session_03_walkthrough.py
```

The walkthrough creates a fresh entry under both policies, then shows the poisoning surface directly: an unsolicited announcement overwrites a known mapping under `ACCEPT_ALL`, and the identical announcement is refused — MAC unchanged — under `ONLY_IF_KNOWN`. It also shows a solicited `CONFIRMED` reply and an unsolicited reply landing on an `INCOMPLETE` entry.

## Done When

The learner can say all of the following without looking at notes:

- "ARP has no authentication, so process_announcement()'s policy argument is the only thing standing between an unsolicited announcement and a cache overwrite."
- "ACCEPT_ALL lets any announcement overwrite any known mapping — that's the spoofing surface, plainly."
- "ONLY_IF_KNOWN refuses unsolicited overwrites of known mappings, but still allows new entries and completions of in-flight resolutions — it's a mitigation, not real DAI."

## References

- RFC 826 (An Ethernet Address Resolution Protocol)
- RFC 5227 Section 1 (IPv4 Address Conflict Detection — gratuitous ARP as an announcement mechanism, the context this toy's `ArpAnnouncement` borrows its shape from)
