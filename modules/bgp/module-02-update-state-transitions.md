# Module 02: How UPDATE Changes State

## Core Question

How does a BGP UPDATE change routing state?

## Read It Like Code

```text
apply_update(prefix, attrs)
withdraw(prefix)
```

## Key Idea

An UPDATE is not just "a packet with route information".

It is an operation that mutates routing state.

## Teaching Goal

The learner should be able to explain:

- the difference between NLRI and Withdrawn Routes
- why announcement and withdrawal are different operations
- why a route disappearing is not the same as a session dying
- why attributes travel with the route advertisement

## References

- RFC 4271 Section 3.1
- RFC 4271 Section 4.3
- RFC 4271 Section 5
