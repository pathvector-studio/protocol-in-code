# Session 06 / Module 06: CNAME Restarts the Question

## Position

- Track: DNS
- Session: 06
- Site lesson: `pathvector-site/courses/protocols-in-code/dns/module-06/index.html`
- Source file: `src/protocol_in_code/dns/cname.py`
- Walkthrough script: `examples/dns/session_06_walkthrough.py`

## Core Question

A CNAME is not an A record. How does asking for an A record still end at one, and what stops the chain from running forever?

## Outcome

By the end of this session, the learner should be able to:

- explain a CNAME as a name substitution, not an answer
- trace a multi-hop chain from alias to final records
- name the two guards that bound the loop: the seen-set and the length limit
- distinguish a dangling CNAME from a CNAME loop

## Read Order

1. Read `ChainResult`
2. Read `follow_cname()` top to bottom
3. Run `examples/dns/session_06_walkthrough.py`
4. Trace the loop scenario by hand and find the exact line that catches it

## Read It Like Code

```python
follow_cname(
    qname,
    qtype,
    records_by_name,
    max_chain,
)
```

## Values That Matter

| Value | Why it matters |
|---|---|
| `(current, qtype)` lookup | The original question, re-asked at each hop. The type never changes. |
| `(current, "CNAME")` lookup | The substitution rule. Only consulted when the real question has no answer. |
| `seen` | Every name visited so far. Revisiting one means a loop, and loops must be detected, not survived. |
| `max_chain` | The budget. Even loop-free chains must end. |

## Chain Loop

```text
look up (name, qtype)      -> found?    answer, stop
look up (name, CNAME)      -> missing?  dead end, stop
target already seen?       -> loop, stop
otherwise                  -> name := target, repeat (bounded)
```

## Reading Lens

The important move in this session is to stop reading a CNAME as "an alias record in the answer" and start asking:

- what is the current name at this hop?
- did the question or only the name change?
- which guard would fire if this zone data were misconfigured?

## Toy Model Boundary

Real resolvers receive the CNAME and the final records in one response when the same server knows both, and they cache each link of the chain separately. This lesson makes every hop explicit so the restart structure is visible.

`records_by_name` is a flat dict. Session 08 replaces it with the zone walk from Session 02, which is where a CNAME crossing into another zone becomes real work.

## Code Landmarks

### `ChainResult.chain`

The list of names the question passed through. Length 1 means no CNAME was involved.

### The order of the two lookups

The real type is checked before CNAME at every hop. A name that has both an A record and a CNAME answers with the A record here — and in real DNS, that dual state is itself illegal.

### The `seen` set

Loop detection is a membership test. Without it, `loop-a -> loop-b -> loop-a` would consume the entire chain budget and misreport as "limit reached" instead of "loop".

## Failure Questions

Use the source file to answer these:

1. Why does the walkthrough's `direct.example.com` scenario have a chain of length 1?
2. What does `stopped_because` say for a CNAME whose target has no records at all?
3. How does the code distinguish a loop from a merely long chain?
4. Why does `qtype` stay constant while `current` changes?
5. What would break if `seen` started empty instead of containing the first name?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/dns/session_06_walkthrough.py
```

The walkthrough prints each chain hop by hop, including a dangling target and a two-name loop.

## Done When

The learner can say all of the following without looking at notes:

- "A CNAME replaces the name and asks the same question again."
- "The chain ends in exactly one of four ways: answer, dead end, loop, or budget."
- "Loop detection needs memory of visited names. A step counter alone cannot tell a loop from a long chain."

## References

- RFC 1034 Section 3.6.2
- RFC 1034 Section 5.2.2
- RFC 6604 (xNAME RCODE clarifications)
