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

2. `modules/bgp/module-02-update-state-transitions.md`
   - Question: How does UPDATE change routing state?
   - Lens: mutation functions + state transitions

3. `modules/bgp/module-03-best-path-if-statements.md`
   - Question: Why does one path become best?
   - Lens: ordered condition branches

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
