# Session 02 / Module 02: Cost Decides the Path to Root

## Position

- Track: STP
- Session: 02
- Site lesson: `pathvector-site/courses/protocols-in-code/stp/module-02/index.html`
- Source file: `src/protocol_in_code/stp/path_cost.py`
- Walkthrough script: `examples/stp/session_02_walkthrough.py`

## Core Question

Every bridge now agrees who the root is (Session 01). If a bridge has more than one port that could eventually reach the root, which one does it pick, and what exactly gets added up along the way?

## Outcome

By the end of this session, the learner should be able to:

- recite the 802.1D port cost table and explain why cost falls as link speed rises
- state which port's speed `accumulate()` charges cost to, and why that side is the common point of confusion
- name the three-stage tiebreak `better_path()` runs, in order, and what each stage compares
- explain why `better_path()` is written as three separate branches instead of one tuple comparison

## Read Order

1. Read the module docstring at the top of the file
2. Read `PORT_COST`
3. Read `PathToRoot`
4. Read `accumulate()`
5. Read `better_path()`
6. Run `examples/stp/session_02_walkthrough.py`

## Read It Like Code

```python
PathToRoot(
    root_path_cost,
    neighbor_bridge,
    neighbor_port_id,
)
```

## Fields That Matter

| Field | Why it matters |
|---|---|
| `root_path_cost` | The primary ranking key — the total accumulated cost of this path back to the root. |
| `neighbor_bridge` | First tiebreak. The `BridgeId` of the neighbor this path was heard from, compared with `bridge_id_lt()` from Session 01 — lowest wins, same inversion. |
| `neighbor_port_id` | Second tiebreak, only reached when the same neighbor is heard on two parallel links. |

## Decision Flow

```text
better_path(a, b):
  a.root_path_cost != b.root_path_cost  -> lower root_path_cost wins
  a.neighbor_bridge != b.neighbor_bridge -> bridge_id_lt(a.neighbor_bridge, b.neighbor_bridge) wins
  otherwise                              -> lower neighbor_port_id wins
```

## Reading Lens

The important move in this session is to stop reading `PORT_COST` as a lookup table you memorize and start asking:

- which port's speed does a given cost number belong to — the one a BPDU left on, or the one it arrived on?
- when two paths tie on cost, what's actually being compared next — is it still about cost at all?
- how many separate `if` branches does it take to express "cost, then neighbor bridge, then port," and why not fold all three into one tuple like `bridge_id_lt()` does?

`better_path()` deliberately does *not* collapse into a single tuple comparison the way Session 01's `bridge_id_lt()` did. The docstring says so directly: each stage is "a separate branch so the priority order is visible rather than folded into one tuple comparison." Compare the two styles side by side — same idea (rank by a sequence of keys, break ties in order), different presentation, and the source is explicit about why it chose this one for `better_path()`.

## Toy Model Boundary

Real 802.1D bridges also compare BPDU message age against a configured max age, apply a "hello lost" timeout, and — since 802.1D-2004 — use a revised, higher-precision port cost table with values up to 200,000,000 for very high speeds. `PORT_COST` here only has four entries (10, 100, 1000, 10000 Mbps) and any other speed simply raises a `KeyError` — this toy stops at "how does cost accumulate and break ties," not "how does a bridge handle a speed nobody configured for."

`accumulate()` and `better_path()` both take their inputs as plain arguments rather than reading from any shared mutable state, which is what keeps every scenario in the walkthrough reproducible and order-independent.

## Code Landmarks

### `PORT_COST`

The literal 802.1D table: `{10: 100, 100: 19, 1000: 4, 10000: 2}`. Read the numbers, not just the keys — cost falls as speed rises, so a 10 Gbps hop (cost 2) is fifty times cheaper than a 10 Mbps hop (cost 100). This is the mechanism that makes a spanning tree prefer high-bandwidth paths without any explicit "prefer bandwidth" rule — it falls straight out of minimizing `root_path_cost`.

### `accumulate()`'s docstring — the receiving-side charge

The single most important sentence in this file: cost accumulates on the **receiving** side, not the sending side. A BPDU advertises the cost of the path from the root down to its sender; the bridge that hears it adds the cost of the link it just arrived on, then advertises that new total onward. The docstring flags this directly as "a common point of confusion" — it's tempting to think the port that transmits is the one being charged, but 802.1D charges the port that receives.

### `better_path()`'s three stages

Read the three `if`/`return` pairs as an ordered checklist, not a single expression: stage 1 is cost, stage 2 is `bridge_id_lt()` on `neighbor_bridge` (the same lowest-wins comparison from Session 01, reused here rather than reimplemented), stage 3 is `neighbor_port_id` — reached only when the same neighbor bridge is heard on two parallel links to this one.

## Failure Questions

Use the source file to answer these:

1. `PORT_COST[10]` and `PORT_COST[10000]` — which is larger, and what does that ordering say about how 802.1D wants a spanning tree to route traffic?
2. `accumulate(path, ingress_speed_mbps)` adds `PORT_COST[ingress_speed_mbps]` to `path.root_path_cost`. Is `ingress_speed_mbps` the speed of the port the BPDU was sent from, or the port it just arrived on? Which sentence in the docstring says so directly?
3. Two `PathToRoot` values have equal `root_path_cost` and equal `neighbor_bridge`. Which field does `better_path()` compare next, and what does it take for two paths to even reach that third stage?
4. Two `PathToRoot` values have equal `root_path_cost` but different `neighbor_bridge`. Which function decides the winner, and does `better_path()` reimplement that comparison or call into Session 01's module?
5. `better_path()` is written as three sequential `if` statements rather than one `(cost, neighbor_bridge, port_id)` tuple comparison. According to the docstring, why does the source choose this style here?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/stp/session_02_walkthrough.py
```

The walkthrough asserts two `PORT_COST` values directly (10 Mbps vs. 1 Gbps, "faster is cheaper"), runs `accumulate()` across two hops to show cost building on the receiving side each time, and constructs `better_path()` pairs that differ at exactly one stage — cost, then neighbor bridge, then port ID — to exercise all three tiebreaks in order.

## Done When

The learner can say all of the following without looking at notes:

- "PORT_COST falls as speed rises — a spanning tree prefers fast links because fast links are cheap, not because of any separate bandwidth rule."
- "Cost is charged on the port a BPDU arrives on, not the port it left from — that's the opposite of what most people guess on first read."
- "better_path() is cost first, then neighbor bridge ID (lowest wins, same as Session 01), then neighbor port ID — three explicit stages, not one folded tuple."

## References

- IEEE 802.1D (the standard defining the port cost table and path cost comparison; no RFC governs STP)
