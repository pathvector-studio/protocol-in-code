# Session 05 / Module 05: Build the Toy Shaper Loop

## Position

- Track: QoS
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/qos/module-05/index.html`
- Source file: `src/protocol_in_code/qos/shaper_loop.py`
- Walkthrough script: `examples/qos/session_05_walkthrough.py`

## Core Question

Four sessions built four standalone mechanisms — a token bucket that refills itself, the lazy refill math underneath it, a leaky bucket that drains itself, and a class tree that validates its own shape. None of them, alone, shapes traffic. What does it take to wire them into something that classifies a packet and decides its fate, and what exactly is it about that wiring that keeps one class's exhaustion from leaking into another's?

## Outcome

By the end of this session, the learner should be able to:

- name every field on `ToyShaper` and which earlier session's module owns the mechanism behind it
- trace `enqueue()`'s three steps — classify, refill, spend — and say which function from which session each step calls
- explain why `run_contention()` proves isolation, and say precisely what would have to change in `ToyShaper` for that isolation to break
- predict, from the source alone, what `enqueue()` does when asked about a class name that isn't in `self.buckets`
- read `shaper.trace` as the record of what actually happened, the same way `ToyTcpEndpoint.trace` worked in the TCP track's capstone

## Read Order

1. Read the module docstring at the top of `shaper_loop.py`
2. Read the `import` block — four names from three sibling modules
3. Read `EnqueueResult`
4. Read `ToyShaper`'s field list
5. Read `tick()`
6. Read `enqueue()`
7. Read `run_contention()` and its docstring
8. Run `examples/qos/session_05_walkthrough.py`

## Read It Like Code

```python
ToyShaper(
    tree,
    buckets,
    clock,
    trace,
)
```

## Parts List

Every field and every function `shaper_loop.py` imports was taught by an earlier session in this track. The capstone's only new code is the wiring between them.

| Import | Session that taught it | What it contributes to `ToyShaper` |
|---|---|---|
| `classes.ClassTree` | 04 | `tree` — describes how class names relate to each other. `ToyShaper` stores it but `enqueue()` never actually consults it; see Toy Model Boundary. |
| `token_bucket.TokenBucket`, `try_consume`, `ConsumeOutcome` | 01 | `buckets` — one `TokenBucket` per class name; `enqueue()`'s entire accept/throttle decision is a direct call to `try_consume()`. |
| `refill.compute_refill` (via `token_bucket.try_consume`, not imported directly) | 02 | The lazy-refill arithmetic that fires every time `try_consume()` runs — `shaper_loop.py` never calls it itself, `try_consume()` does, on the caller's behalf. |
| `leaky_bucket.LeakyBucket`, `offer`, `OfferOutcome` | 03 | Not part of `ToyShaper` at all — used only in the module's own `__main__` block to run the same burst through a leaky bucket side-by-side, for comparison. |

## Decision Flow

```text
enqueue(class_name, size, now):
  1. bucket = self.buckets[class_name]      # classify: plain dict lookup, no fallback
  2. consumed = try_consume(bucket, size, now)   # Session 01+02's refill-then-spend
  3. append one line to self.trace describing class_name, size, now, outcome, tokens_remaining
  4. return EnqueueResult(class_name, consumed.outcome, consumed.tokens_remaining)

run_contention(shaper, offered):
  for each (class_name, size) in offered, in order:
    call shaper.enqueue(class_name, size, shaper.clock)   # same clock value every time
  return all results as a tuple
```

## Reading Lens

The important move in this session is to stop asking "what does the shaper do" and start asking, at every line: which earlier session's mechanism is actually doing the work here, and which parts of `ToyShaper` are just bookkeeping around it?

- in `enqueue()`, which line is Session 01's code, verbatim, and which lines are new to this module?
- in `run_contention()`, `shaper.clock` is read once per offer but never advanced between offers — what does that tell you about what "the same instant" means in this toy?
- when `bucket` in `enqueue()` is looked up, what enforces that this bucket belongs to `class_name` and not some other class? (Look at what `self.buckets` actually is.)

## Toy Model Boundary

There is no queue, no scheduler, and no delay — every `enqueue()` call is an instantaneous accept-or-throttle decision against one class's own bucket balance, exactly like Session 01's `try_consume()` in isolation. Nothing here models a packet waiting, being reordered, or being dequeued later; `THROTTLED` means the offer was rejected outright, not queued for a retry.

`ToyShaper` carries a `tree: ClassTree` field, but `enqueue()` never reads it. The class hierarchy from Session 04 — and the `borrowable()` computation that comes with it — is not wired into the shaping decision at all in this toy. A class that is THROTTLED on its own bucket does not borrow from its parent's slack, even though `borrowable()` could, in principle, say slack exists. Wiring `borrowable()` into `enqueue()` would be the natural next step past this course, and it is exactly the gap between this toy and a real HTB-style shaper: real HTB lets a class actually draw on a parent's spare capacity when its own bucket runs dry; here, `guaranteed_rate` and the class tree describe an intended hierarchy but never touch a single token.

There is one shared `clock: int` on `ToyShaper`, moved only by `tick()`; `run_contention()` does not advance it between offers, which is what makes "the same instant" a precise, reproducible claim in the walkthrough rather than an approximation.

## Code Landmarks

### The module docstring's second paragraph

Names the headline directly: "one class exhausting its bucket must not affect another class's bucket, because each class owns an independent TokenBucket keyed by name." Read this before `run_contention()` so the function reads as a proof of a stated claim, not just a demo.

### `enqueue()`'s first line

`bucket = self.buckets[class_name]` — a plain dict index, not `.get()` with a default. There is no branch here for a class name that isn't a key.

### `enqueue()`'s trace line

Every call appends to `self.trace` regardless of outcome — `THROTTLED` calls are logged exactly as `ALLOWED` calls are. The trace is a complete record, not a log of successes.

### `run_contention()`'s docstring

Spells out the exact scenario the walkthrough runs: video's bucket drained low, bulk's untouched, `now` held constant — and states the expected result before the code runs it.

### The `__main__` block's leaky-bucket comparison

After proving isolation, the block runs the identical burst through a fresh `LeakyBucket` from Session 03 and gets the opposite outcome — `OVERFLOWED` where the token bucket said `ALLOWED`. This is not part of `ToyShaper`'s own logic; it is the module reaching back to tie Session 01 and Session 03 together one more time.

## Failure Questions

Use the source file to answer these:

1. `enqueue()` does `bucket = self.buckets[class_name]` with no existence check. If `class_name` is not a key in `self.buckets`, what exception is raised, and at which exact line does it happen — inside `enqueue()`, or inside some function it calls?
2. `run_contention()`'s scenario throttles `video` and allows `bulk` in the same call. Point to the single field on `ToyShaper` whose type (`dict[str, TokenBucket]`, one bucket per name) is the entire reason video's throttle cannot touch bulk's balance. What would have to change about that field's type for isolation to break?
3. `ToyShaper.tree` is populated with a full class hierarchy in the walkthrough (`default` / `video` / `bulk`) but `enqueue()` never reads `self.tree`. If a class is `THROTTLED` on its own bucket while `borrowable()` (Session 04) would report slack available from its parent, does anything in this module route that slack to the throttled class?
4. `run_contention()` calls `shaper.enqueue(class_name, size, shaper.clock)` for every offer in the tuple, reading `shaper.clock` fresh each time but never calling `shaper.tick()` between offers. If `offered` contains two entries for the same class name, do they see the same token balance as of the start of the call, or does the first offer's consumption affect the second's outcome?
5. The `__main__` block builds a `LeakyBucket` with `capacity=20, level=20` — already full — and offers it the same 10-unit burst that a fresh `TokenBucket` allows. Read `offer()` in `leaky_bucket.py`: why does an already-full leaky bucket reject a burst that an already-full token bucket would allow?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/qos/session_05_walkthrough.py
```

The walkthrough builds a shaper with two classes — `video` nearly drained (5 of 20 tokens) and `bulk` at full capacity — and runs `run_contention()` at a single instant to show video `THROTTLED` while bulk sails through `ALLOWED`, proving isolation. It then advances the clock and retries video to show the same bucket that was just throttled re-allowing once time has passed. It calls `enqueue()` with a class name that was never registered in `self.buckets` and confirms the real code's actual behavior — a `KeyError`, not a graceful `THROTTLED` result. Finally it checks that `shaper.trace` is non-empty and contains the exact throttle line from the first contention check.

## Done When

The learner can say all of the following without looking at notes:

- "A shaper is not a new algorithm — it's Session 01's token bucket, one per class, wired to a classify step and a trace."
- "Isolation between classes comes from each class owning its own TokenBucket object, not from any scheduling or ordering trick."
- "This toy's class tree from Session 04 is stored but never consulted — borrowing on paper and borrowing in the shaping decision are two different things here."

## References

- RFC 2475 (An Architecture for Differentiated Services) — the general framing of sorting traffic into classes with distinct treatment, which this shaper implements in miniature for one node.
- This module's per-class hierarchical shaping is HTB-flavored (Hierarchical Token Bucket, as implemented in Linux `tc`), but only in shape: real HTB performs live borrowing, letting a class draw on a parent's spare bandwidth as actual usage shifts. `ToyShaper` stores a `ClassTree` but `enqueue()` never reads it — no borrowing, live or otherwise, happens in this toy's shaping decision.
