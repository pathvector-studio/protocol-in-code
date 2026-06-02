# Session 09 / Module 09: Session Loss and Recompute

## Position

- Track: BGP
- Session: 09
- Site lesson: `pathvector-site/courses/protocols-in-code/bgp/module-09/index.html`
- Source file: `src/protocol_in_code/bgp/recompute.py`
- Walkthrough script: `examples/bgp/session_09_walkthrough.py`

## Core Question

What happens to Loc-RIB when one peer disappears and the best path came from that peer?

## Outcome

By the end of this session, the learner should be able to:

- explain why peer loss removes more than one route at once
- explain why Loc-RIB may need recomputation after peer loss
- explain why the next-best path can become installed
- explain why a prefix may disappear completely if no alternative path remains

## Bridge From Previous Sessions

Session 06 introduced per-peer received state. Session 09 uses that model to show why "peer down" is not a single route event but a set of withdrawals followed by best-path recomputation.

## Read Order

1. Read `recompute_best_path_for_prefix()`
2. Read `handle_peer_loss()`
3. Notice how lost prefixes are collected from one peer
4. Notice how each affected prefix is recomputed independently
5. Run `examples/bgp/session_09_walkthrough.py`

## Read It Like Code

```python
lost_prefixes = tuple(adj_rib_in.paths_by_peer.get(peer_id, {}).keys())
adj_rib_in.paths_by_peer.pop(peer_id, None)

for prefix in lost_prefixes:
    results[prefix] = recompute_best_path_for_prefix(adj_rib_in, loc_rib, prefix)
```

## Data That Matters

| Item | Why it matters |
|---|---|
| `lost_prefixes` | A peer session loss affects every prefix learned from that peer. |
| `build_candidates()` | Rebuilds the candidate set from surviving peers only. |
| `select_best_path()` | Chooses the replacement path if one exists. |
| `remove_best_path()` | Cleans Loc-RIB when no path remains. |

## Failure Questions

1. Why is peer loss modeled as multiple recomputations?
2. When does Loc-RIB remove a prefix entirely?
3. When does a backup path become best?
4. Which store changes first: Adj-RIB-In or Loc-RIB?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/bgp/session_09_walkthrough.py
```

The walkthrough installs a best path from one peer, simulates that peer going down, and shows the backup path taking over.

## Done When

The learner can say all of the following without looking at notes:

- "Peer loss first deletes Adj-RIB-In state for that peer."
- "Then each affected prefix is recomputed."
- "A backup path can become best."
- "If no backup exists, the Loc-RIB entry disappears."
