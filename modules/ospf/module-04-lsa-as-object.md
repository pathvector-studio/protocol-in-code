# Session 04: LSA As An Object

## Question

What does a Router-LSA have to contain before flood and SPF can use it?

## Source

- `src/protocol_in_code/ospf/lsa.py`

## Read Order

1. Read `LSAHeader`.
2. Read `LinkDescription` and `StubNetwork`.
3. Read `RouterLSA`.
4. Read `router_lsa_key()` and `is_newer_lsa()`.

## Walkthrough

```bash
PYTHONPATH=src python3 examples/ospf/session_04_walkthrough.py
```

## Done When

- You can point to the fields that identify a Router-LSA.
- You can separate transit links from reachable stub networks.

