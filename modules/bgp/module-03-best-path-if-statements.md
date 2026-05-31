# Module 03: Best Path Selection As If Statements

## Core Question

Why does one BGP path become best?

## Read It Like Code

```text
if weight_a != weight_b:
  choose_higher_weight()
else if local_pref_a != local_pref_b:
  choose_higher_local_pref()
else if as_path_len_a != as_path_len_b:
  choose_shorter_as_path()
else:
  keep_comparing()
```

## Key Idea

Best path selection should be read as an ordered decision flow.

It is not enough to say "BGP preferred this route".

The learner should identify the first condition that produced the winner.

## Teaching Goal

The learner should be able to explain:

- why multiple paths are required before this logic matters
- how comparison order changes the result
- why best does not automatically mean authorized or safe
- how competing paths become a debugging exercise

## References

- RFC 4271 Section 3
- RFC 4271 Section 5
- RFC 4271 Section 9
- RFC 7908
