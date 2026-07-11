# Protocol in Code

Protocol in Code is an intermediate course for reading network protocols as logic.

日本語: Protocol in Code は、ネットワークプロトコルを「設定例」ではなく「入力・状態・条件分岐を持つロジック」として読むための中級コースです。

This repository is intentionally separate from `protocol-lab`.

- `protocol-lab`: beginner, hands-on-first, containerlab-centered course
- `protocol-in-code`: intermediate, logic-first, code-reading-centered course

## Tracks

The course is organized as tracks: one protocol per track, each ending with a
"Build the toy X loop" capstone. A track spans three directories with the same name:
`modules/<track>/`, `src/protocol_in_code/<track>/`, and `examples/<track>/`.

日本語: このコースは「トラック」単位で構成されています。1プロトコル=1トラックで、
最終セッションは恒例の "Build the toy X loop"。各トラックは同名の3ディレクトリ
（modules / src / examples）にまたがります。

| Track | Status | Sessions |
|---|---|---|
| BGP | Published | 15 |
| OSPF | Published | 12 |
| DNS | Published | 8 |
| TCP | Published | 11 |
| TLS | Published | 9 |
| HTTP/QUIC | Published | 10 |

`COURSE_MAP.md` is the canonical map of published tracks. `IDEAS.md` is the generation
queue: full session plans for planned tracks and candidates beyond them.

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

### DNS

- Session 01: A query is a question object
- Session 02: The resolver walks down the tree
- Session 03: Delegation is a referral, not an answer
- Session 04: The cache answers first
- Session 05: TTL is a clock, not a config
- Session 06: CNAME restarts the question
- Session 07: Failure has flavors
- Session 08: Build the toy resolver loop

### TCP

- Session 01: A segment carries the conversation state
- Session 02: It takes three packets to say hello
- Session 03: Sequence numbers wrap around
- Session 04: The window is how much room you have
- Session 05: The timer learns the network
- Session 06: Three duplicates mean loss
- Session 07: cwnd is just a variable
- Session 08: Out of order is not lost
- Session 09: Goodbye takes four packets (and a wait)
- Session 10: RST ends everything now
- Session 11: Build the toy TCP loop

### TLS

- Session 01: Hello lists everything you can do
- Session 02: Agreement is a set intersection
- Session 03: Keys grow on a schedule
- Session 04: Trust is a walk up the chain
- Session 05: A cert is for a name, not a server
- Session 06: Resumption is a cache hit
- Session 07: The record layer is an envelope
- Session 08: Failure is a typed message
- Session 09: Build the toy handshake loop

### HTTP/QUIC

- Session 01: A request is parsed text
- Session 02: Headers come with rules
- Session 03: Keep-alive is a pool
- Session 04: Cacheable is a decision tree
- Session 05: Redirects are a bounded loop
- Session 06: Chunked is a parser state machine
- Session 07: Streams share one connection
- Session 08: QUIC streams don't block each other
- Session 09: Flow control is a credit balance
- Session 10: Build the toy HTTP server loop

## Repository Layout

| Path | Purpose |
|---|---|
| `src/protocol_in_code/<track>/` | Source files that the course explains module by module, one directory per track |
| `modules/<track>/` | Course modules (sessions), one directory per track |
| `examples/<track>/` | Runnable per-session walkthroughs, one directory per track |
| `notes/` | Short design notes |
| `COURSE_MAP.md` | Canonical map of published tracks and their modules |
| `IDEAS.md` | Generation queue: session plans for planned tracks and candidate tracks |

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

The DNS sessions currently map like this:

- Session 01 -> `src/protocol_in_code/dns/query.py`
- Session 02 -> `src/protocol_in_code/dns/walk.py`
- Session 03 -> `src/protocol_in_code/dns/referral.py`
- Session 04 -> `src/protocol_in_code/dns/cache.py`
- Session 05 -> `src/protocol_in_code/dns/ttl.py`
- Session 06 -> `src/protocol_in_code/dns/cname.py`
- Session 07 -> `src/protocol_in_code/dns/failures.py`
- Session 08 -> `src/protocol_in_code/dns/resolver.py`

The TCP sessions currently map like this:

- Session 01 -> `src/protocol_in_code/tcp/segment.py`
- Session 02 -> `src/protocol_in_code/tcp/handshake.py`
- Session 03 -> `src/protocol_in_code/tcp/seqnum.py`
- Session 04 -> `src/protocol_in_code/tcp/window.py`
- Session 05 -> `src/protocol_in_code/tcp/rto.py`
- Session 06 -> `src/protocol_in_code/tcp/fast_retransmit.py`
- Session 07 -> `src/protocol_in_code/tcp/congestion.py`
- Session 08 -> `src/protocol_in_code/tcp/reassembly.py`
- Session 09 -> `src/protocol_in_code/tcp/teardown.py`
- Session 10 -> `src/protocol_in_code/tcp/reset.py`
- Session 11 -> `src/protocol_in_code/tcp/speaker.py`

The TLS sessions currently map like this:

- Session 01 -> `src/protocol_in_code/tls/messages.py`
- Session 02 -> `src/protocol_in_code/tls/negotiate.py`
- Session 03 -> `src/protocol_in_code/tls/key_schedule.py`
- Session 04 -> `src/protocol_in_code/tls/chain.py`
- Session 05 -> `src/protocol_in_code/tls/hostname.py`
- Session 06 -> `src/protocol_in_code/tls/resumption.py`
- Session 07 -> `src/protocol_in_code/tls/record.py`
- Session 08 -> `src/protocol_in_code/tls/alert.py`
- Session 09 -> `src/protocol_in_code/tls/handshake_loop.py`

The HTTP/QUIC sessions currently map like this (one track, two source packages):

- Session 01 -> `src/protocol_in_code/http/parse.py`
- Session 02 -> `src/protocol_in_code/http/headers.py`
- Session 03 -> `src/protocol_in_code/http/pool.py`
- Session 04 -> `src/protocol_in_code/http/caching.py`
- Session 05 -> `src/protocol_in_code/http/redirect.py`
- Session 06 -> `src/protocol_in_code/http/chunked.py`
- Session 07 -> `src/protocol_in_code/http/h2_streams.py`
- Session 08 -> `src/protocol_in_code/quic/streams.py`
- Session 09 -> `src/protocol_in_code/quic/flow_control.py`
- Session 10 -> `src/protocol_in_code/http/server_loop.py`

## Separation Rule

Do not treat this repository as a companion appendix to `protocol-lab`.

`protocol-lab` should stand on its own for beginner learners.

`protocol-in-code` should stand on its own for intermediate learners who want to read protocol behavior as logic.
