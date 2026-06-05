# Protocol in Code

Protocol in Code is an intermediate course for reading network protocols as logic.

日本語: Protocol in Code は、ネットワークプロトコルを「設定例」ではなく「入力・状態・条件分岐を持つロジック」として読むための中級コースです。

This repository is intentionally separate from `protocol-lab`.

- `protocol-lab`: beginner, hands-on-first, containerlab-centered course
- `protocol-in-code`: intermediate, logic-first, code-reading-centered course

## Current Focus

The current published subjects are BGP and OSPF.

### BGP

- Session 01: What a BGP neighbor needs
- Session 02: How UPDATE changes state
- Session 03: Best path selection as if statements
- Session 04: Origin validation is a separate decision
- Session 05: Validation state does not act by itself
- Session 06: Where routes live
- Session 07: Import policy rewrites inputs
- Session 08: Export policy decides what leaves
- Session 09: Session loss and recompute
- Session 10: One route through the whole pipeline
- Session 11: Peer state gates UPDATE
- Session 12: Export refresh after recompute
- Session 13: Event dispatches announce, withdraw, and peer down
- Session 14: One prefix becomes a decision set
- Session 15: Build the toy speaker loop

### OSPF

- Session 01: Hello starts the neighbor
- Session 02: Neighbor state machine
- Session 03: DR and BDR election
- Session 04: LSA as an object
- Session 05: Flooding decides where the LSA goes
- Session 06: LSDB keeps the version
- Session 07: SPF turns the LSDB into a tree
- Session 08: The tree becomes routes
- Session 09: Cost picks the winner
- Session 10: Topology change recomputes the RIB
- Session 11: Area boundaries rewrite the view
- Session 12: Build the toy OSPF speaker loop

## Repository Layout

| Path | Purpose |
|---|---|
| `src/protocol_in_code/bgp/` | BGP source files that the site explains module by module |
| `src/protocol_in_code/ospf/` | OSPF source files that the site explains module by module |
| `modules/` | Core course modules |
| `notes/` | Short design notes, draft ideas, and future topics |
| `COURSE_MAP.md` | Canonical map of tracks and modules |

## Course Shape

Each module should answer one question in a code-like way.

Examples:

- What inputs are required?
- What state changes when a message arrives?
- What condition decides the branch?
- What output is produced?

## Source of Truth Split

- GitHub repository: the code itself
- pathvector.dev: the explanations, module framing, and reading guidance

The BGP sessions currently map like this:

- Session 01 -> `src/protocol_in_code/bgp/session.py`
- Session 02 -> `src/protocol_in_code/bgp/update.py`
- Session 03 -> `src/protocol_in_code/bgp/best_path.py`
- Session 04 -> `src/protocol_in_code/bgp/validation.py`
- Session 05 -> `src/protocol_in_code/bgp/policy.py`
- Session 06 -> `src/protocol_in_code/bgp/ribs.py`
- Session 07 -> `src/protocol_in_code/bgp/import_policy.py`
- Session 08 -> `src/protocol_in_code/bgp/export_policy.py`
- Session 09 -> `src/protocol_in_code/bgp/recompute.py`
- Session 10 -> `src/protocol_in_code/bgp/pipeline.py`
- Session 11 -> `src/protocol_in_code/bgp/peer_state.py`
- Session 12 -> `src/protocol_in_code/bgp/export_refresh.py`
- Session 13 -> `src/protocol_in_code/bgp/events.py`
- Session 14 -> `src/protocol_in_code/bgp/decision_process.py`
- Session 15 -> `src/protocol_in_code/bgp/speaker.py`

The OSPF sessions currently map like this:

- Session 01 -> `src/protocol_in_code/ospf/hello.py`
- Session 02 -> `src/protocol_in_code/ospf/neighbor.py`
- Session 03 -> `src/protocol_in_code/ospf/dr_election.py`
- Session 04 -> `src/protocol_in_code/ospf/lsa.py`
- Session 05 -> `src/protocol_in_code/ospf/flooding.py`
- Session 06 -> `src/protocol_in_code/ospf/lsdb.py`
- Session 07 -> `src/protocol_in_code/ospf/spf.py`
- Session 08 -> `src/protocol_in_code/ospf/routing.py`
- Session 09 -> `src/protocol_in_code/ospf/cost.py`
- Session 10 -> `src/protocol_in_code/ospf/recompute.py`
- Session 11 -> `src/protocol_in_code/ospf/areas.py`
- Session 12 -> `src/protocol_in_code/ospf/speaker.py`

## Separation Rule

Do not treat this repository as a companion appendix to `protocol-lab`.

`protocol-lab` should stand on its own for beginner learners.

`protocol-in-code` should stand on its own for intermediate learners who want to read protocol behavior as logic.
