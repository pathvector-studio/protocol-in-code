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

11. `modules/bgp/module-11-peer-state-gates-updates.md`
    - Question: When should the control plane accept or ignore an UPDATE?
    - Lens: session gate + established-only writes
    - Source: `src/protocol_in_code/bgp/peer_state.py`

12. `modules/bgp/module-12-export-refresh-after-recompute.md`
    - Question: How does a Loc-RIB change become per-peer advertise or withdraw?
    - Lens: desired outbound state + Adj-RIB-Out reconciliation
    - Source: `src/protocol_in_code/bgp/export_refresh.py`

13. `modules/bgp/module-13-event-dispatch.md`
    - Question: How do announce, withdraw, and peer-down events choose different control-plane branches?
    - Lens: event dispatcher + per-event recompute flow
    - Source: `src/protocol_in_code/bgp/events.py`

14. `modules/bgp/module-14-prefix-decision-set.md`
    - Question: How does one prefix become a policy-aware decision set across many peers?
    - Lens: candidate evaluation loop + best among installable paths
    - Source: `src/protocol_in_code/bgp/decision_process.py`

15. `modules/bgp/module-15-build-the-toy-speaker-loop.md`
    - Question: What does the smallest readable BGP speaker look like?
    - Lens: object state + event handlers + export refresh loop
    - Source: `src/protocol_in_code/bgp/speaker.py`

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
