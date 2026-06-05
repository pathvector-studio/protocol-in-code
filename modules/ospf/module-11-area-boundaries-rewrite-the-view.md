# Session 11: Area Boundaries Rewrite The View

## Question

What changes when routes cross an area boundary through an ABR-like summary step?

## Source

- `src/protocol_in_code/ospf/areas.py`

## Read Order

1. Read `SummaryLSA`.
2. Read `summarize_area_routes()`.
3. Read `import_summary_lsas()`.

## Bridge From Previous Session

Session 10 left us with best internal routes after recompute.
This session rewrites that internal view across an area boundary instead of extending the LSDB/SPF pipeline itself.

## Walkthrough

```bash
PYTHONPATH=src python3 examples/ospf/session_11_walkthrough.py
```

## Simplification Note

This is a summary-route teaching model, not a full ABR implementation.
The receiving side adds `cost to ABR` to the advertised summary metric, and summary import stays a post-SPF branch in this first arc.

## Done When

- You can explain what is preserved from the source area.
- You can explain what gets rewritten for the target area.
