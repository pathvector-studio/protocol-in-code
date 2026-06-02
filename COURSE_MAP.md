# Course Map

## Positioning

- Beginner course: `protocol-lab`
- Intermediate course: `protocol-in-code`

Both are independent tracks.

## Current Track

### BGP

1. `modules/bgp/module-01-neighbor-inputs.md`
   - Question: What does a BGP neighbor need in order to form?
   - Lens: function inputs + state machine
   - Source: `src/protocol_in_code/bgp/session.py`

2. `modules/bgp/module-02-update-state-transitions.md`
   - Question: How does UPDATE change routing state?
   - Lens: mutation functions + state transitions
   - Source: `src/protocol_in_code/bgp/update.py`

3. `modules/bgp/module-03-best-path-if-statements.md`
   - Question: Why does one path become best?
   - Lens: ordered condition branches
   - Source: `src/protocol_in_code/bgp/best_path.py`

4. `modules/bgp/module-04-origin-validation.md`
   - Question: How is origin authorization decided after best path selection?
   - Lens: separate validation function + tri-state outcome
   - Source: `src/protocol_in_code/bgp/validation.py`

5. `modules/bgp/module-05-policy-after-validation.md`
   - Question: What does the router do with valid / invalid / not_found after validation?
   - Lens: policy function + explicit action output
   - Source: `src/protocol_in_code/bgp/policy.py`

6. `modules/bgp/module-06-where-routes-live.md`
   - Question: Where do received, selected, and advertised routes live?
   - Lens: Adj-RIB-In + Loc-RIB + Adj-RIB-Out
   - Source: `src/protocol_in_code/bgp/ribs.py`

7. `modules/bgp/module-07-import-policy-rewrites-inputs.md`
   - Question: How does import policy rewrite or reject paths before best-path?
   - Lens: input transformation + early drop
   - Source: `src/protocol_in_code/bgp/import_policy.py`

8. `modules/bgp/module-08-export-policy-decides-what-leaves.md`
   - Question: Why is the exported route not always identical to the installed route?
   - Lens: outbound rewrite + per-peer advertisement decision
   - Source: `src/protocol_in_code/bgp/export_policy.py`

9. `modules/bgp/module-09-session-loss-and-recompute.md`
   - Question: What happens when a peer disappears and Loc-RIB must recompute?
   - Lens: per-peer cleanup + replacement path selection
   - Source: `src/protocol_in_code/bgp/recompute.py`

10. `modules/bgp/module-10-one-route-through-the-pipeline.md`
    - Question: How does one route move through the whole toy control plane?
    - Lens: integration pipeline + end-to-end object flow
    - Source: `src/protocol_in_code/bgp/pipeline.py`

## Future Tracks

### DNS

- recursive resolution as a function chain
- cache lookup as state + TTL logic

### TCP

- handshake as state machine
- retransmission as timeout + branch logic

### TLS

- handshake as negotiated capabilities
- certificate validation as decision flow

### HTTP / QUIC

- request lifecycle as layered function calls
- stream selection and multiplexing as stateful logic
