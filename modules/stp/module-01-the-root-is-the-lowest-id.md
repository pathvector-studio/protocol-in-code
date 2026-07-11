# Session 01 / Module 01: The Root Is the Lowest ID

## Position

- Track: STP
- Session: 01
- Site lesson: `pathvector-site/courses/protocols-in-code/stp/module-01/index.html`
- Source file: `src/protocol_in_code/stp/root_election.py`
- Walkthrough script: `examples/stp/session_01_walkthrough.py`

## Core Question

Every bridge on a LAN could claim to be the root of the spanning tree. What single comparison decides which one actually is, and why does that comparison run backwards from every other election in this course?

## Outcome

By the end of this session, the learner should be able to:

- name the exact tuple `elect_root()` compares candidates on, in order
- state which direction wins the comparison, and say why that direction is the opposite of OSPF's DR election and VRRP's master election
- explain how an unconfigured network can elect its oldest switch as root by accident
- explain why explicit priority configuration exists and what it overrides

## Read Order

1. Read the module docstring at the top of the file
2. Read `DEFAULT_PRIORITY`'s docstring
3. Read `_mac_key()`
4. Read `BridgeId`
5. Read `bridge_id_lt()`
6. Read `elect_root()`
7. Run `examples/stp/session_01_walkthrough.py`

## Read It Like Code

```python
BridgeId(
    priority,
    mac,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `priority` | The primary ranking key. Defaults to 32768 for every bridge that hasn't been configured otherwise. |
| `mac` | The tiebreak key. Unique per bridge, so it always resolves a tie — and it's the field that turns an unconfigured network into an accident. |

## Decision Flow

```text
bridge_id_lt(a, b):
  compare (a.priority, mac_key(a.mac)) < (b.priority, mac_key(b.mac))
  lower tuple wins  ("a < b" means "a is MORE preferred")

elect_root(bridge_ids):
  compare every bridge on (priority, mac_key(mac))
  return the min
```

## Reading Lens

The important move in this session is to stop reading `elect_root()` as "just another max-of-a-tuple election" and start asking:

- what is the comparison key, and is it a single value or a tuple?
- which direction wins — the biggest tuple or the smallest?
- what happens when every bridge on the network ties on the first element?

This is the same election-by-comparison shape as OSPF's `dr_election.py` (ranks on `(priority, router_id)`, takes `max()`) and VRRP's `ha/vrrp_election.py` (ranks on `(priority, primary_ip)`, takes `max()`). STP builds the identical shape — a `(priority, id)` tuple — and then takes `min()` instead. There is no protocol reason for the flip; 802.1D simply defined "more preferred" as "numerically smaller" where OSPF and VRRP defined it as "numerically bigger." The module docstring calls this out explicitly as "a classic source of off-by-inversion bugs when porting election logic" between the three — read `bridge_id_lt()`'s docstring, which says outright that `a < b` here means "a is MORE preferred," and that this reads backwards next to the other two modules on purpose.

## Toy Model Boundary

Real STP elects a root through BPDUs exchanged and re-compared as the network converges, with hello timers, message age, and max age all governing when a bridge accepts a claim versus falls back to claiming itself. None of that exists here — `elect_root()` assumes it is handed the full candidate set at once, the same simplification VRRP's `elect()` makes and OSPF's DR election makes. This module stops at "which BridgeId wins the comparison," not "how bridges agree on the candidate set in the first place."

## Code Landmarks

### The module docstring

States the inversion as the whole thesis of the file: OSPF and VRRP take `max()` of `(priority, id)`; STP takes `min()` of the same shape. "Elsewhere 'more preferred' means 'numerically bigger'; in spanning tree it means 'numerically smaller.'" Read this before anything else — every other landmark in this file is downstream of that one sentence.

### `DEFAULT_PRIORITY`'s docstring

32768 is 802.1D's factory default. Its docstring names the consequence directly: when every bridge ships with the same default, priority can't break any tie, so MAC is the only thing left to compare — which is exactly how the oldest-switch accident happens.

### `_mac_key()`

Turns `"00:00:00:00:00:0a"` into `(0, 0, 0, 0, 0, 10)` — a tuple of ints, not a string. The same reasoning as `_ip_key()` in VRRP's module: comparing MAC strings lexically would not sort them the way numeric octets do, so the octets are parsed to ints first.

### `bridge_id_lt()`'s docstring

Names itself as "the inversion point" against the other two modules and states plainly that reading `a < b` as "a is MORE preferred" is disorienting on purpose — it is the whole point of this session.

### `elect_root()`'s docstring — the oldest-switch accident

This is the landmark to sit with the longest. At default priority, the tiebreak falls entirely to MAC, and MAC addresses sort low-to-high in manufacture order within a vendor block — so the bridge that has been running longest tends to have the lowest MAC and becomes root purely by accident, not by design. The docstring states the fix in the same breath: a network operator who wants a specific bridge at the root sets that bridge's priority below `DEFAULT_PRIORITY`, which wins the comparison before MAC is ever consulted. Explicit priority isn't a nice-to-have — it's how a human overrides an accident that happens by default.

## Failure Questions

Use the source file to answer these:

1. `bridge_id_lt(a, b)` builds `(a.priority, _mac_key(a.mac)) < (b.priority, _mac_key(b.mac))`. If two bridges have the same priority, which element of the tuple decides the comparison, and what does `_mac_key()` turn the MAC into before that comparison runs?
2. Two bridges are both left at `DEFAULT_PRIORITY`. Structurally, which one becomes root, and why does the docstring call this "by accident" rather than "by design"?
3. A bridge is configured with `priority=100` and every other bridge on the network is at `DEFAULT_PRIORITY` (32768). Can any other bridge ever win `elect_root()` against it, regardless of MAC? Why not, structurally?
4. `elect_root()` calls `min()`, not `max()`. If someone copy-pasted OSPF's `dr_election.py` election function and only swapped in `BridgeId`, what single change would they need to make for the STP election to behave correctly, per the module docstring?
5. `elect_root()` takes a `tuple[BridgeId, ...]` and returns a single `BridgeId`. What would happen if it were called with an empty tuple — is that guarded anywhere in this file?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/stp/session_01_walkthrough.py
```

The walkthrough elects a root between two default-priority bridges to show the oldest-switch accident, then shows an explicit low priority overriding a low MAC, exercises `bridge_id_lt()` in both directions, and runs `elect_root()` over three bridges.

## Done When

The learner can say all of the following without looking at notes:

- "STP's election is the same `(priority, id)` shape as OSPF and VRRP, but it takes `min()` where they take `max()` — there's no protocol reason, it's just what the standard picked."
- "If every bridge is left at default priority, the network elects its oldest switch as root by accident, because MAC is the only thing left to break the tie."
- "Explicit priority configuration exists specifically to let a human override that accident before MAC is ever consulted."

## References

- IEEE 802.1D (the standard governing STP root bridge election; no RFC governs STP)
