# Session 12: Build The Toy OSPF Speaker Loop

## Question

What does the smallest readable OSPF speaker look like when Hello, LSDB, SPF, and area summary are connected?

## Source

- `src/protocol_in_code/ospf/speaker.py`

## Read Order

1. Read `SpeakerInterface`.
2. Read `SpeakerStep`.
3. Read `ToyOSPFSpeaker`.
4. Read `run_dr_election()`, `receive_hello()`, `complete_database_exchange()`, `originate_router_lsa()`, `receive_router_lsa()`, `summarize_to_area()`, and `import_summaries()`.

## Bridge From Previous Sessions

- Session 01-02 gave us adjacency gates.
- Session 03 gave us shared-segment election state.
- Session 04-06 gave us LSA shape, flooding scope, and LSDB storage.
- Session 07-10 gave us SPF, route derivation, and recompute.
- Session 11 gave us cross-area summary handling.
- This session wraps those pieces into one gated speaker-shaped object.

## Walkthrough

```bash
PYTHONPATH=src python3 examples/ospf/session_12_walkthrough.py
```

## Simplification Note

This is still a teaching model.
It does not model packet encoding, full retransmission, or every OSPF packet type.
It also keeps the first arc router-only by omitting Network-LSA and transit-network vertices.

## Done When

- You can explain the speaker as state plus a few gated event-shaped methods.
- You can see where Hello, database exchange completion, local Router-LSA origination, remote Router-LSA receive, flood scope, summary creation, and summary import each enter the loop.
