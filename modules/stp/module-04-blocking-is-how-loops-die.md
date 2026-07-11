# Session 04 / Module 04: Blocking Is How Loops Die

## Position

- Track: STP
- Session: 04
- Site lesson: `pathvector-site/courses/protocols-in-code/stp/module-04/index.html`
- Source file: `src/protocol_in_code/stp/blocking.py`
- Walkthrough script: `examples/stp/session_04_walkthrough.py`

## Core Question

Ethernet frames have no TTL, so a loop floods forever — what exact comparison decides which port stops forwarding, and why is that comparison enough to break every loop in the topology?

## Outcome

By the end of this session, the learner should be able to:

- state the four-step BPDU comparison in order, and explain why each step is a separate branch instead of one tuple comparison
- explain why `should_block()` is just `bpdu_is_superior()` pointed in a specific direction
- trace the worked triangle's one interesting collision — C's port to A — and say which step decides it
- explain why a direct link to the root can still end up blocked

## Read Order

1. Read the module docstring's worked triangle in full
2. Read `Bpdu`
3. Read `bpdu_is_superior()`
4. Read `should_block()`
5. Run `examples/stp/session_04_walkthrough.py`

## Read It Like Code

```python
Bpdu(
    root_id,
    root_path_cost,
    sender_bridge,
    sender_port,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `root_id` | The claim to the root's identity. Step 1 of the comparison and it decides outright whenever the two BPDUs disagree. |
| `root_path_cost` | How far the sender claims to be from that root. Only consulted once `root_id` is tied. |
| `sender_bridge` | Who is speaking. Only consulted once root and cost are both tied — this is the step that resolves the worked triangle. |
| `sender_port` | Which port the sender used. The last resort, for when the same bridge is heard on two of our ports. |

## Decision Flow

```text
bpdu_is_superior(a, b):
  root_id differs        -> lower root_id wins                  (step 1)
  root_id tied,
    root_path_cost differs -> lower root_path_cost wins          (step 2)
  cost also tied,
    sender_bridge differs  -> lower sender_bridge id wins        (step 3)
  sender_bridge also tied  -> lower sender_port wins              (step 4)

should_block(heard, mine):
  bpdu_is_superior(heard, mine) -> True  => port BLOCKS
  otherwise                     -> False => port stays open
```

## Reading Lens

The important move in this session is to stop reading `bpdu_is_superior()` as an abstract ranking function and start asking, for a specific port on a specific segment:

- what BPDU would I send on this port if I forwarded? (`mine`)
- what BPDU do I actually hear on this port? (`heard`)
- which of the four steps is the one that actually differs between them?

Every other step being tied is not an edge case — on a real segment shared by only two speakers, three of the four steps are *usually* tied, and the whole outcome rides on whichever step finally differs.

## Toy Model Boundary

Real 802.1D BPDUs also carry a bridge's designated-port ID, message age, max age, hello time, and forward delay, and the comparison includes port-role bookkeeping (Designated vs. Root vs. Alternate) that this module leaves entirely to `port_roles.py`. This module isolates just the comparison — four fields, four branches — so the tiebreak logic can be read without the rest of the protocol's state machine in the way. There is no timer here: `bpdu_is_superior()` is pure, called with two already-known BPDUs, not with a live stream of hellos arriving over time.

## Code Landmarks

### The module docstring's worked triangle

The single most important paragraph in this file. It walks the same three-bridge topology `stp_loop.py`'s `triangle()` builds in code, and it names the one segment (`seg-ca`) where the comparison actually has to do work — the other two segments (`seg-ab`, `seg-bc`) have only one non-root speaker each, so nothing there can lose a tiebreak.

### `bpdu_is_superior()`'s four `if`/`return` steps

Written as four explicit branches rather than one `(root_id, root_path_cost, sender_bridge, sender_port)` tuple comparison. The comment above the function numbers them 1 through 4 for a reason: each step is a separate question a bridge is asking, and the walkthrough exercises each one in isolation.

### `should_block()`'s one-line body

`return bpdu_is_superior(heard, mine)`. There is no separate blocking algorithm — blocking *is* the comparison, evaluated with a specific pair of arguments in a specific order.

## Failure Questions

Use the source file to answer these:

1. In the worked triangle, C hears A's BPDU directly on the C-A segment, and C would also re-advertise its own BPDU on that same segment. Which of the four steps in `bpdu_is_superior()` is the one that actually decides between them — the earlier three all being tied?
2. Why does the C-A segment need a real comparison at all, while `seg-ab` and `seg-bc` do not?
3. `should_block(heard, mine)` calls `bpdu_is_superior(heard, mine)` — not the reverse argument order. What would swapping the arguments mean operationally?
4. Step 4 of `bpdu_is_superior()` compares `sender_port`. Under what circumstance would two BPDUs ever reach step 4 with the same `sender_bridge`?
5. `Bpdu` is a frozen dataclass with no timestamp or age field. What does that tell you about what `bpdu_is_superior()` does and does not know about how fresh a BPDU is?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/stp/session_04_walkthrough.py
```

The walkthrough constructs one crafted BPDU pair per comparison step — root_id, then root_path_cost, then sender_bridge, then sender_port — each pair identical on every earlier step so only the one under test can decide the outcome. It then runs `should_block()` in both directions on the same pair, and finally reproduces the docstring's exact triangle collision: A's direct BPDU on `seg-ca` versus C's re-advertisement of its own path to A, tied on root and cost, decided by `sender_bridge`.

## Done When

The learner can say all of the following without looking at notes:

- "The four steps are checked in order — root id, then cost, then sender bridge, then sender port — and the first one that differs decides everything."
- "should_block is just bpdu_is_superior with the heard BPDU as the challenger and my own BPDU as the incumbent."
- "In the worked triangle, C's port to A blocks because the tiebreak reaches sender_bridge, and A's own id beats C's — even though C's port is a direct link to the root."

## References

- IEEE 802.1D (no RFC governs the Spanning Tree Protocol; it is defined entirely in the IEEE 802.1D standard)
