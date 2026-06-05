# Session 06: LSDB Keeps The Version

## Question

How does the LSDB decide whether a newly received Router-LSA replaces the old one?

## Source

- `src/protocol_in_code/ospf/lsdb.py`

## Read Order

1. Read `LinkStateDatabase`.
2. Read `install_router_lsa()`.
3. Read `router_lsas()`.

## Walkthrough

```bash
PYTHONPATH=src python3 examples/ospf/session_06_walkthrough.py
```

## Done When

- You can explain why same-sequence older information is ignored.
- You can explain why the LSDB is grouped by area.

