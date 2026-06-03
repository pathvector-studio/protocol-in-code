# Session 12: Export Refresh After Recompute

## Question

When `Loc-RIB` changes, how do outbound advertisements get refreshed per peer?

## Source

- `src/protocol_in_code/bgp/export_refresh.py`
- Companion source: `src/protocol_in_code/bgp/export_policy.py`

## Read Order

1. Read `ExportTarget` and notice that export is peer-specific.
2. Read `refresh_exports_for_prefix()` and follow the three values for one peer: `current`, `installed`, `desired`.
3. Watch the branch where `desired` is `None`: that is where a withdrawal appears in `Adj-RIB-Out`.

## Bridge From Previous Sessions

- Session 08 explained how one installed route becomes one exported route.
- Session 09 explained how `Loc-RIB` can change after loss and recompute.
- This session connects those two facts.

## Code Lens

```python
current = current_by_prefix.get(prefix)
desired = prepare_export(installed, target.peer_type, target.policy)

if desired is None:
    current_by_prefix.pop(prefix, None)
else:
    current_by_prefix[prefix] = desired
```

This is the point where outbound state is reconciled.

## Walkthrough

Run:

```bash
PYTHONPATH=src python3 examples/bgp/session_12_walkthrough.py
```

Look for:

- an advertisement to the customer peer
- no advertisement to the denied upstream peer
- a withdrawal when the installed path disappears

## Simplification Note

This toy model refreshes one prefix at a time and does not build incremental UPDATE packets.
It only shows the decision about what `Adj-RIB-Out` should contain.

## Done When

- You can explain why export refresh is a separate pass after recompute.
- You can tell whether a peer should see an advertise or a withdraw by looking at `current` and `desired`.
