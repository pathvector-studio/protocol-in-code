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
