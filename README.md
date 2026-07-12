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
| Packet Parser | Published | 5 |
| RPKI | Published | 5 |
| DHCP | Published | 6 |
| RIP | Published | 6 |
| NAT | Published | 6 |
| ARP/ND | Published | 4 |
| QoS | Published | 5 |
| Load Balancer | Published | 6 |
| NTP | Published | 4 |
| HA (VRRP+BFD) | Published | 4 |
| ICMP | Published | 5 |
| DNSSEC | Published | 5 |
| TCP2 (Operational TCP) | Published | 6 |
| STP | Published | 5 |
| ICE | Published | 5 |
| IGMP | Published | 4 |
| Same Shape | Published | 5 |

`COURSE_MAP.md` is the canonical map of published tracks. `IDEAS.md` is the generation
queue: full session plans for planned tracks and candidates beyond them.

**Don't read the tracks in table order.** See [`LEARNING_PATHS.md`](LEARNING_PATHS.md)
for genre groupings, goal-based roadmaps (web engineer / infra / security / SRE), the
complete-beginner entry point, and the Protocol Lab ↔ Protocol in Code cross-reference.

日本語: トラックを表の順に読む必要はありません。ジャンル分け・目的別ロードマップ・
初心者の入口・Protocol Lab との対応表は [`LEARNING_PATHS.md`](LEARNING_PATHS.md) へ。

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

### Packet Parser

- Session 01: Bytes have a shape
- Session 02: Peel one layer, find the next
- Session 03: Bits don't align to bytes
- Session 04: The checksum is arithmetic, not magic
- Session 05: Build the toy pcap reader

### RPKI

- Session 01: A ROA is a permission slip
- Session 02: Covering is prefix math
- Session 03: Three verdicts, not two
- Session 04: Policy decides what a verdict means
- Session 05: Build the toy validator loop

### DHCP

- Session 01: Discovery is shouting into the dark
- Session 02: An offer is a proposal with a deadline
- Session 03: The pool hands out what's free
- Session 04: A lease is a dict with an expiry
- Session 05: Renewal happens before the end
- Session 06: Build the toy DHCP server loop

### RIP

- Session 01: A route is a rumor with a distance
- Session 02: Bellman-Ford is a for loop
- Session 03: Sixteen means unreachable
- Session 04: Rumors can circle back
- Session 05: Don't tell me what I told you
- Session 06: Build the toy RIP loop

### NAT

- Session 01: A connection is a 5-tuple
- Session 02: Translation is a rewrite function
- Session 03: The reply finds its way back
- Session 04: Ports are a shared resource
- Session 05: State expires, again
- Session 06: Build the toy NAT box loop

### ARP/ND

- Session 01: The cache has moods
- Session 02: Packets wait for answers
- Session 03: Anyone can answer
- Session 04: Build the toy ARP responder loop

### QoS

- Session 01: A token bucket is two variables
- Session 02: Refill is lazy
- Session 03: Leaky and token are cousins
- Session 04: Classes form a tree
- Session 05: Build the toy shaper loop

### Load Balancer

- Session 01: Round robin is one index
- Session 02: Least connections is a counter
- Session 03: Hashing keeps you on the same server
- Session 04: The ring survives a server change
- Session 05: Health is a state machine
- Session 06: Build the toy load balancer loop

### NTP

- Session 01: Four timestamps, two unknowns
- Session 02: Stratum is depth in a tree
- Session 03: Symmetry is an assumption
- Session 04: Build the toy NTP client loop

### HA (VRRP+BFD)

- Session 01: The highest priority speaks
- Session 02: Silence means failure
- Session 03: Three states, both directions
- Session 04: Build the toy failover loop

### ICMP

- Session 01: An error is a packet about a packet
- Session 02: Unreachable has flavors
- Session 03: TTL is a hop budget
- Session 04: Time exceeded draws the map
- Session 05: Build the toy traceroute loop

### DNSSEC

- Session 01: A signature rides beside the record
- Session 02: The key signs the key
- Session 03: DS links child to parent
- Session 04: Validation walks up the tree
- Session 05: Build the toy validating resolver

### TCP2 (Operational TCP)

- Session 01: TIME_WAIT is a promise with a price
- Session 02: SYN cookies are stateless memory
- Session 03: Nagle and delayed ACK deadlock
- Session 04: Keepalive probes an idle line
- Session 05: The backlog is two queues
- Session 06: Build the toy connection janitor

### STP

- Session 01: The root is the lowest ID
- Session 02: Cost decides the path to root
- Session 03: Ports have roles
- Session 04: Blocking is how loops die
- Session 05: Build the toy spanning tree loop

### ICE

- Session 01: STUN tells you your own address
- Session 02: NATs have personalities
- Session 03: Candidates are gathered, not chosen
- Session 04: Pairs are checked in priority order
- Session 05: Build the toy connectivity check loop

### IGMP

- Session 01: Group membership is a set
- Session 02: Queries keep the set honest
- Session 03: Snooping reads someone else's mail
- Session 04: Build the toy querier loop

### Same Shape

- Session 01: The expiring dict, five times
- Session 02: Election is a comparison function, five times
- Session 03: Three states beat two
- Session 04: Silence means failure, everywhere
- Session 05: Every protocol ends in a loop

## Repository Layout

| Path | Purpose |
|---|---|
| `src/protocol_in_code/<track>/` | Source files that the course explains module by module, one directory per track |
| `modules/<track>/` | Course modules (sessions), one directory per track |
| `examples/<track>/` | Runnable per-session walkthroughs, one directory per track |
| `notes/` | Short design notes |
| `COURSE_MAP.md` | Canonical map of published tracks and their modules |
| `LEARNING_PATHS.md` | Genre map, goal-based roadmaps, and the Protocol Lab cross-reference |
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

The Packet Parser sessions currently map like this:

- Session 01 -> `src/protocol_in_code/parser/ethernet.py`
- Session 02 -> `src/protocol_in_code/parser/dispatch.py`
- Session 03 -> `src/protocol_in_code/parser/ip.py`
- Session 04 -> `src/protocol_in_code/parser/checksum.py`
- Session 05 -> `src/protocol_in_code/parser/pcap_loop.py`

The RPKI sessions currently map like this:

- Session 01 -> `src/protocol_in_code/rpki/roa.py`
- Session 02 -> `src/protocol_in_code/rpki/covering.py`
- Session 03 -> `src/protocol_in_code/rpki/validate.py`
- Session 04 -> `src/protocol_in_code/rpki/policy.py`
- Session 05 -> `src/protocol_in_code/rpki/validator_loop.py`

The DHCP sessions currently map like this:

- Session 01 -> `src/protocol_in_code/dhcp/discover.py`
- Session 02 -> `src/protocol_in_code/dhcp/offer.py`
- Session 03 -> `src/protocol_in_code/dhcp/pool.py`
- Session 04 -> `src/protocol_in_code/dhcp/leases.py`
- Session 05 -> `src/protocol_in_code/dhcp/renewal.py`
- Session 06 -> `src/protocol_in_code/dhcp/server_loop.py`

The RIP sessions currently map like this:

- Session 01 -> `src/protocol_in_code/rip/route.py`
- Session 02 -> `src/protocol_in_code/rip/update.py`
- Session 03 -> `src/protocol_in_code/rip/infinity.py`
- Session 04 -> `src/protocol_in_code/rip/count_to_infinity.py`
- Session 05 -> `src/protocol_in_code/rip/split_horizon.py`
- Session 06 -> `src/protocol_in_code/rip/speaker.py`

The NAT sessions currently map like this:

- Session 01 -> `src/protocol_in_code/nat/five_tuple.py`
- Session 02 -> `src/protocol_in_code/nat/rewrite.py`
- Session 03 -> `src/protocol_in_code/nat/table.py`
- Session 04 -> `src/protocol_in_code/nat/ports.py`
- Session 05 -> `src/protocol_in_code/nat/timeout.py`
- Session 06 -> `src/protocol_in_code/nat/nat_loop.py`

The ARP/ND sessions currently map like this:

- Session 01 -> `src/protocol_in_code/arp/cache.py`
- Session 02 -> `src/protocol_in_code/arp/pending.py`
- Session 03 -> `src/protocol_in_code/arp/gratuitous.py`
- Session 04 -> `src/protocol_in_code/arp/responder_loop.py`

The QoS sessions currently map like this:

- Session 01 -> `src/protocol_in_code/qos/token_bucket.py`
- Session 02 -> `src/protocol_in_code/qos/refill.py`
- Session 03 -> `src/protocol_in_code/qos/leaky_bucket.py`
- Session 04 -> `src/protocol_in_code/qos/classes.py`
- Session 05 -> `src/protocol_in_code/qos/shaper_loop.py`

The Load Balancer sessions currently map like this:

- Session 01 -> `src/protocol_in_code/lb/round_robin.py`
- Session 02 -> `src/protocol_in_code/lb/least_conn.py`
- Session 03 -> `src/protocol_in_code/lb/hash_pick.py`
- Session 04 -> `src/protocol_in_code/lb/ring.py`
- Session 05 -> `src/protocol_in_code/lb/health.py`
- Session 06 -> `src/protocol_in_code/lb/lb_loop.py`

The NTP sessions currently map like this:

- Session 01 -> `src/protocol_in_code/ntp/offset.py`
- Session 02 -> `src/protocol_in_code/ntp/stratum.py`
- Session 03 -> `src/protocol_in_code/ntp/asymmetry.py`
- Session 04 -> `src/protocol_in_code/ntp/client_loop.py`

The HA (VRRP+BFD) sessions currently map like this:

- Session 01 -> `src/protocol_in_code/ha/vrrp_election.py`
- Session 02 -> `src/protocol_in_code/ha/vrrp_timeout.py`
- Session 03 -> `src/protocol_in_code/ha/bfd.py`
- Session 04 -> `src/protocol_in_code/ha/failover_loop.py`

The ICMP sessions currently map like this:

- Session 01 -> `src/protocol_in_code/icmp/message.py`
- Session 02 -> `src/protocol_in_code/icmp/unreachable.py`
- Session 03 -> `src/protocol_in_code/icmp/ttl.py`
- Session 04 -> `src/protocol_in_code/icmp/probing.py`
- Session 05 -> `src/protocol_in_code/icmp/trace_loop.py`

The DNSSEC sessions currently map like this:

- Session 01 -> `src/protocol_in_code/dnssec/rrsig.py`
- Session 02 -> `src/protocol_in_code/dnssec/dnskey.py`
- Session 03 -> `src/protocol_in_code/dnssec/ds.py`
- Session 04 -> `src/protocol_in_code/dnssec/chain.py`
- Session 05 -> `src/protocol_in_code/dnssec/validator_loop.py`

The TCP2 (Operational TCP) sessions currently map like this:

- Session 01 -> `src/protocol_in_code/tcp2/time_wait_cost.py`
- Session 02 -> `src/protocol_in_code/tcp2/syn_cookies.py`
- Session 03 -> `src/protocol_in_code/tcp2/nagle_delack.py`
- Session 04 -> `src/protocol_in_code/tcp2/keepalive.py`
- Session 05 -> `src/protocol_in_code/tcp2/backlog.py`
- Session 06 -> `src/protocol_in_code/tcp2/janitor_loop.py`

The STP sessions currently map like this:

- Session 01 -> `src/protocol_in_code/stp/root_election.py`
- Session 02 -> `src/protocol_in_code/stp/path_cost.py`
- Session 03 -> `src/protocol_in_code/stp/port_roles.py`
- Session 04 -> `src/protocol_in_code/stp/blocking.py`
- Session 05 -> `src/protocol_in_code/stp/stp_loop.py`

The ICE sessions currently map like this:

- Session 01 -> `src/protocol_in_code/ice/stun.py`
- Session 02 -> `src/protocol_in_code/ice/nat_behavior.py`
- Session 03 -> `src/protocol_in_code/ice/candidates.py`
- Session 04 -> `src/protocol_in_code/ice/checklist.py`
- Session 05 -> `src/protocol_in_code/ice/ice_loop.py`

The IGMP sessions currently map like this:

- Session 01 -> `src/protocol_in_code/igmp/membership.py`
- Session 02 -> `src/protocol_in_code/igmp/querier.py`
- Session 03 -> `src/protocol_in_code/igmp/snooping.py`
- Session 04 -> `src/protocol_in_code/igmp/querier_loop.py`

The Same Shape sessions currently map like this:

- Session 01 -> `src/protocol_in_code/meta/expiring_state.py`
- Session 02 -> `src/protocol_in_code/meta/election.py`
- Session 03 -> `src/protocol_in_code/meta/tristate.py`
- Session 04 -> `src/protocol_in_code/meta/silence.py`
- Session 05 -> `src/protocol_in_code/meta/the_loop.py`

## Separation Rule

Do not treat this repository as a companion appendix to `protocol-lab`.

`protocol-lab` should stand on its own for beginner learners.

`protocol-in-code` should stand on its own for intermediate learners who want to read protocol behavior as logic.
