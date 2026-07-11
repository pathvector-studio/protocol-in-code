# Session 05 / Module 05: Build the Toy Connectivity Check Loop

## Position

- Track: ICE
- Session: 05
- Site lesson: `pathvector-site/courses/protocols-in-code/ice/module-05/index.html`
- Source file: `src/protocol_in_code/ice/ice_loop.py`
- Walkthrough script: `examples/ice/session_05_walkthrough.py`

## Core Question

Four sessions built STUN discovery, NAT personality classification, candidate gathering, and priority-ordered checklists separately. What does it look like when two agents run all of that against each other, end to end, against a NAT they never had to understand?

## Outcome

By the end of this session, the learner should be able to:

- name every function `ice_loop.py` imports and which earlier session's module owns it
- trace `run_ice()`'s four phases — gather, exchange, form checklist, check and nominate — in order
- explain why a reflexive-candidate pair wins when both NATs are simple, and why the same strategy fails when both NATs are address-and-port-dependent
- read a full ICE trace and say, line by line, what happened and why

## Read Order

1. Read the module comment above `ToyIceAgent`
2. Read `ToyIceAgent` and `IceReport`
3. Read `run_ice()` top to bottom
4. Read `scenario_direct_fails()`
5. Read `scenario_hard_nats()`
6. Run `examples/ice/session_05_walkthrough.py`

## Read It Like Code

```python
ToyIceAgent(
    name,
    candidates,
    trace,
)
```

## Parts List

Every function `ice_loop.py` imports was taught by an earlier session in this track. The capstone's only new code is the wiring between them — the same shape as the TCP track's Session 11.

| Import | Session that taught it | What it contributes to `run_ice()` |
|---|---|---|
| `stun.py`'s `BindingResponse` (via `candidates.gather`) | 01 | The observed mapped address each agent's server-reflexive candidate is built from — STUN's one job, discovering what the outside world sees. |
| `nat_behavior.py`'s `classify_mapping`, `MappingBehavior` | 02 | Not called directly by `ice_loop.py`, but the reason `scenario_hard_nats()`'s `Connectivity` looks the way it does — an address-and-port-dependent NAT is exactly what makes every reflexive pairing fail. |
| `candidates.py`'s `Candidate`, `CandidateType`, `gather` | 03 | `ToyIceAgent.candidates` — `run_ice()`'s first act is calling `gather()` indirectly (each scenario builds its agents by calling it) to turn one local address, one STUN response, and one optional TURN allocation into a tuple of candidates. |
| `checklist.py`'s `CandidatePair`, `ChecklistResult`, `Connectivity`, `form_checklist`, `run_checklist` | 04 | The ordered plan and the check-and-nominate loop — `run_ice()` calls `form_checklist()` once and `run_checklist()` once, then re-walks the same pairs to build the trace. |
| `nat/nat_loop.py`'s `ToyNatBox` | (NAT track) | Not imported here at all — and that absence is the point. This track's toy NAT (`nat/nat_loop.py`) allocates one translated tuple per 5-tuple, making it address-and-port-dependent by construction, the hardest personality for peer-to-peer. ICE's answer to a NAT box it cannot see inside is not to model it — it is to stop predicting and just try every candidate pair in priority order. `scenario_hard_nats()` is this track's answer to that box. |

## Decision Flow

```text
run_ice(agent_a, agent_b, reality):
  1. trace agent_a's gathered candidates, then agent_b's
  2. trace the exchange: each agent "received" the other's candidate list
  3. pairs = form_checklist(agent_a.candidates, agent_b.candidates)
       -> trace the full priority order as one line
  4. result = run_checklist(pairs, reality)
  5. re-walk pairs in the same order, tracing each check:
       pair is result.nominated -> trace "-> SUCCEEDED (nominated)", stop
       otherwise                -> trace "-> FAILED", continue
  6. result.nominated is None -> trace "checklist exhausted"
  7. return IceReport(nominated_pair, trace)
```

## Reading Lens

The important move in this session is to stop reading `checklist.py` and `candidates.py` as separate demos and start asking, at every line of `run_ice()`:

- which earlier session's function is doing the actual work on this line?
- does this line know anything about NAT behavior, or is it just following the priority order the checklist already fixed?
- what does the trace say happened, and would that trace alone tell a debugger why a particular pair won?

## Toy Model Boundary

`run_ice()` has no STUN connectivity-check messages and no credentials — Session 04's `check_pair()` is a `Connectivity` lookup, not a wire exchange, so nothing here demonstrates the actual STUN Binding request/response pairs RFC 8445 §7 uses to test a pair. There is no trickle ICE: both agents' candidate lists are complete before `form_checklist()` ever runs. There is no controlling/controlled role negotiation beyond the tie bit `pair_priority()` takes as a plain argument — real ICE agents negotiate that role and can detect and resolve conflicts. And the relay is free here: `scenario_hard_nats()` gives both agents a TURN allocation with no cost, no bandwidth limit, and no possibility the allocation itself fails — in reality a relay is the expensive last resort precisely because a third party has to carry every byte.

## Code Landmarks

### The module comment above `ToyIceAgent`

"ICE does not understand NATs — it does not classify them, does not predict which pairs will work. It gathers every candidate either side might be reachable at, sorts every possible pairing by a formula that prefers direct routes, and tries them in that order until one works. It is brute force with a priority order, and that is the whole trick." This is the capstone thesis in one paragraph — everything else in the file is the mechanism.

### `run_ice()`'s trace-building loop

The function calls `run_checklist()` once to get the answer, then re-walks `pairs` a second time purely to build a readable trace up to and including the nominated pair. The nomination itself was already decided; this second loop exists only so a human can see the priority order play out failure by failure.

### `scenario_direct_fails()`

Both agents sit behind simple NATs, so their reflexive candidates are stable, predictable public mappings — "the easy case STUN alone was designed for." HOSTxHOST cannot route across two private networks, but a SERVER_REFLEXIVE pairing can, and it is high enough in the priority order to win before any RELAYED pair is even tried.

### `scenario_hard_nats()`

Both agents sit behind address-and-port-dependent NATs — the same personality `nat_behavior.py` names and `nat/nat_loop.py` builds by construction. A reflexive candidate learned by querying a STUN server predicts nothing about the mapping either NAT will produce toward the *other agent*, because the other agent is a different destination than the STUN server was. Every reflexive pairing fails exactly like a host pairing would; only the relay — a third party both sides can reach directly — closes the loop.

## Failure Questions

Use the source file to answer these:

1. `run_ice()` calls `form_checklist()` exactly once but walks `pairs` twice — once inside `run_checklist()`, once again to build the trace. Why does the second walk not risk nominating a different pair than the first?
2. In `scenario_direct_fails()`, `reality.reachable_type_pairs` includes `(RELAYED, RELAYED)` even though a relay is never needed. What would have to be true about the checklist's priority order for that unused entry to matter?
3. In `scenario_hard_nats()`, both agents are given a `turn_addr`. What field on `ToyIceAgent` would be missing a `RELAYED` candidate entirely if `turn_addr` had been `None` instead — and what would `run_ice()`'s outcome be in that case?
4. `Connectivity.reachable_type_pairs` is declared by the *caller* of `run_ice()`, not computed by it. What real-world fact is each scenario's `Connectivity` standing in for?
5. The trace line `"no pair succeeded - connectivity check exhausted the checklist"` only appears under one condition. What is that condition, in terms of `ChecklistResult.nominated`?

## Walkthrough

Run this:

```bash
PYTHONPATH=src python3 examples/ice/session_05_walkthrough.py
```

The walkthrough runs `scenario_direct_fails()` and checks that the nominated pair involves a `SERVER_REFLEXIVE` candidate and that the trace's first check line is `HostxHost -> FAILED`. It then runs `scenario_hard_nats()` and checks that the nominated pair involves a `RELAYED` candidate, that exactly four checks fail before the fifth succeeds, and that the checklist-order trace line lists `HostxHost` first — the priority order never changes just because the NATs are harder; only which pair reality allows to succeed changes. Both scenarios' traces are checked non-empty with both agents' gather lines present.

## Done When

The learner can say all of the following without looking at notes:

- "ICE never classifies a NAT. It gathers every candidate, sorts every pairing by a fixed formula, and tries them in that order until reality says yes."
- "A reflexive candidate is only useful if the mapping it predicts actually holds toward the real peer — against an address-and-port-dependent NAT, it predicts nothing, and only a relay both sides can reach unconditionally closes the loop."
- "The whole track — STUN, NAT classification, candidate gathering, checklists — was building toward one loop that doesn't need to understand the box it's trying to get through."

## References

- RFC 8445 Section 2 (overview — the gather/exchange/check/nominate shape this module implements end to end)
