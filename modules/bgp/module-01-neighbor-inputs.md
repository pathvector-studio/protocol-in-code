# Module 01: What a BGP Neighbor Needs

## Core Question

What inputs are required to form a BGP neighbor?

## Read It Like Code

```text
neighbor(
  peer_as,
  peer_ip,
  local_as,
  tcp_reachable,
  hold_time,
  keepalive_time,
  capabilities
)
```

## Inputs

- `peer_ip`
- `peer_as`
- `local_as`
- TCP reachability
- timer values
- negotiated capabilities

## State Machine

```text
Idle -> Connect -> Active -> OpenSent -> OpenConfirm -> Established
```

## Teaching Goal

The learner should be able to explain:

- why peer IP alone is not enough
- where AS identity matters
- why TCP failure and OPEN failure are different
- what it means for a neighbor to reach `Established`

## References

- RFC 4271 Section 1.1
- RFC 4271 Section 3
- RFC 4271 Section 4.2
