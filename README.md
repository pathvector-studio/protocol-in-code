# Protocol in Code

Protocol in Code is an intermediate course for reading network protocols as logic.

日本語: Protocol in Code は、ネットワークプロトコルを「設定例」ではなく「入力・状態・条件分岐を持つロジック」として読むための中級コースです。

This repository is intentionally separate from `protocol-lab`.

- `protocol-lab`: beginner, hands-on-first, containerlab-centered course
- `protocol-in-code`: intermediate, logic-first, code-reading-centered course

## Current Focus

The first subject is BGP.

- Module 01: What a BGP neighbor needs
- Module 02: How UPDATE changes state
- Module 03: Best path selection as if statements

## Repository Layout

| Path | Purpose |
|---|---|
| `src/protocol_in_code/bgp/` | BGP source files that the site explains module by module |
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

The BGP modules currently map like this:

- Module 01 -> `src/protocol_in_code/bgp/session.py`
- Module 02 -> `src/protocol_in_code/bgp/update.py`
- Module 03 -> `src/protocol_in_code/bgp/best_path.py`

## Separation Rule

Do not treat this repository as a companion appendix to `protocol-lab`.

`protocol-lab` should stand on its own for beginner learners.

`protocol-in-code` should stand on its own for intermediate learners who want to read protocol behavior as logic.
