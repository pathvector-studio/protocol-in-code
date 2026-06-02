# Session 06 / Module 06: Where Routes Live

## Position

- Track: BGP
- Session: 06
- Site lesson: `pathvector-site/courses/protocols-in-code/bgp/module-06/index.html`
- Source file: `src/protocol_in_code/bgp/ribs.py`
- Walkthrough script: `examples/bgp/session_06_walkthrough.py`

## Core Question

Where does a route live inside the router before selection, after selection, and right before advertisement?

## Outcome

By the end of this session, the learner should be able to:

- explain the difference between Adj-RIB-In, Loc-RIB, and Adj-RIB-Out
- explain why multiple received paths can exist before one best path is installed
- explain how `PathAttributes` become `PathCandidate`
- explain why advertisement is a separate store from local installation

## Bridge From Previous Sessions

Session 02 showed UPDATE as state mutation. Session 03 showed best-path selection. Session 06 connects them by answering where those received paths are stored, where the selected path goes, and where outbound advertisements are staged.

## Read Order

1. Read `AdjRIBIn`
2. Read `LocRIB`
3. Read `AdjRIBOut`
4. Read `store_received_path()`
5. Read `build_candidates()`
6. Read `install_best_path()`
7. Read `stage_advertisement()`
8. Run `examples/bgp/session_06_walkthrough.py`

## Read It Like Code

```python
store_received_path(adj_rib_in, peer_id, prefix, attributes)
candidates = build_candidates(adj_rib_in, prefix)
best = select_best_path(candidates)
install_best_path(loc_rib, best)
stage_advertisement(adj_rib_out, peer_id, best)
```

## Data That Matters

| Item | Why it matters |
|---|---|
| `AdjRIBIn.paths_by_peer` | Keeps what each peer told us. |
| `LocRIB.best_paths` | Keeps the path we installed locally. |
| `AdjRIBOut.advertisements_by_peer` | Keeps what we plan to send to each peer. |
| `build_candidates()` | Bridges Session 02 objects into Session 03 objects. |

## Failure Questions

1. Why can Adj-RIB-In contain multiple paths for one prefix?
2. Why does Loc-RIB only keep one best path in this toy model?
3. Why is Adj-RIB-Out separate from Loc-RIB?
4. Where does `origin` become `origin_type`?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/bgp/session_06_walkthrough.py
```

The walkthrough stores two received paths for the same prefix, builds candidates, installs one best path in Loc-RIB, and stages one outbound advertisement.

## Done When

The learner can say all of the following without looking at notes:

- "Adj-RIB-In is per-peer received state."
- "Loc-RIB is the selected local result."
- "Adj-RIB-Out is outbound state, not just a copy of Loc-RIB."
- "`build_candidates()` is the bridge from received attributes to best-path inputs."
