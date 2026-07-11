# Course Map

## Positioning

- Beginner course: `protocol-lab`
- Intermediate course: `protocol-in-code`

Both are independent courses.

## Track Status

The course is organized as **tracks**: one protocol, one directory, one arc that ends with
"Build the toy X loop". Every track lives in three places with the same name:
`modules/<track>/` (the sessions), `src/protocol_in_code/<track>/` (the code being read),
`examples/<track>/` (runnable walkthroughs).

| Track | Status | Modules | Arc |
|---|---|---|---|
| BGP | Published | 15 | route selection and policy as ordered condition branches |
| OSPF | Published | 12 | link state → flooding → SPF → RIB |
| DNS | Published | 8 | recursive resolution as a bounded loop with a cache in front |
| TCP | Published | 11 | connection state, timers, and recovery as explicit variables |
| TLS | Published | 9 | negotiation, trust chains, and key schedules as functions |
| HTTP/QUIC | Published | 10 | parsing, pooling, and multiplexing as stateful logic |
| (10 candidate tracks) | Idea pool | ~51 | see `IDEAS.md` |

Full session plans (titles, Lens, Source) for planned tracks are in [`IDEAS.md`](IDEAS.md) —
the generation queue. A track moves here when its modules are generated.

## Published Tracks

### BGP

1. `modules/bgp/module-01-neighbor-inputs.md`
   - Question: What does a BGP neighbor need in order to form?
   - Lens: function inputs + state machine
   - Source: `src/protocol_in_code/bgp/session.py`

2. `modules/bgp/module-02-update-state-transitions.md`
   - Question: How does UPDATE change routing state?
   - Lens: mutation functions + state transitions
   - Source: `src/protocol_in_code/bgp/update.py`

3. `modules/bgp/module-03-best-path-if-statements.md`
   - Question: Why does one path become best?
   - Lens: ordered condition branches
   - Source: `src/protocol_in_code/bgp/best_path.py`

4. `modules/bgp/module-04-origin-validation.md`
   - Question: How is origin authorization decided after best path selection?
   - Lens: separate validation function + tri-state outcome
   - Source: `src/protocol_in_code/bgp/validation.py`

5. `modules/bgp/module-05-policy-after-validation.md`
   - Question: What does the router do with valid / invalid / not_found after validation?
   - Lens: policy function + explicit action output
   - Source: `src/protocol_in_code/bgp/policy.py`

6. `modules/bgp/module-06-where-routes-live.md`
   - Question: Where do received, selected, and advertised routes live?
   - Lens: Adj-RIB-In + Loc-RIB + Adj-RIB-Out
   - Source: `src/protocol_in_code/bgp/ribs.py`

7. `modules/bgp/module-07-import-policy-rewrites-inputs.md`
   - Question: How does import policy rewrite or reject paths before best-path?
   - Lens: input transformation + early drop
   - Source: `src/protocol_in_code/bgp/import_policy.py`

8. `modules/bgp/module-08-export-policy-decides-what-leaves.md`
   - Question: Why is the exported route not always identical to the installed route?
   - Lens: outbound rewrite + per-peer advertisement decision
   - Source: `src/protocol_in_code/bgp/export_policy.py`

9. `modules/bgp/module-09-session-loss-and-recompute.md`
   - Question: What happens when a peer disappears and Loc-RIB must recompute?
   - Lens: per-peer cleanup + replacement path selection
   - Source: `src/protocol_in_code/bgp/recompute.py`

10. `modules/bgp/module-10-one-route-through-the-pipeline.md`
    - Question: How does one route move through the whole toy control plane?
    - Lens: integration pipeline + end-to-end object flow
    - Source: `src/protocol_in_code/bgp/pipeline.py`

11. `modules/bgp/module-11-peer-state-gates-updates.md`
    - Question: When should the control plane accept or ignore an UPDATE?
    - Lens: session gate + established-only writes
    - Source: `src/protocol_in_code/bgp/peer_state.py`

12. `modules/bgp/module-12-export-refresh-after-recompute.md`
    - Question: How does a Loc-RIB change become per-peer advertise or withdraw?
    - Lens: desired outbound state + Adj-RIB-Out reconciliation
    - Source: `src/protocol_in_code/bgp/export_refresh.py`

13. `modules/bgp/module-13-event-dispatch.md`
    - Question: How do announce, withdraw, and peer-down events choose different control-plane branches?
    - Lens: event dispatcher + per-event recompute flow
    - Source: `src/protocol_in_code/bgp/events.py`

14. `modules/bgp/module-14-prefix-decision-set.md`
    - Question: How does one prefix become a policy-aware decision set across many peers?
    - Lens: candidate evaluation loop + best among installable paths
    - Source: `src/protocol_in_code/bgp/decision_process.py`

15. `modules/bgp/module-15-build-the-toy-speaker-loop.md`
   - Question: What does the smallest readable BGP speaker look like?
   - Lens: object state + event handlers + export refresh loop
   - Source: `src/protocol_in_code/bgp/speaker.py`

### OSPF

1. `modules/ospf/module-01-hello-starts-the-neighbor.md`
   - Question: What has to match before an OSPF Hello can even start a neighbor relationship?
   - Lens: packet fields + first gate
   - Source: `src/protocol_in_code/ospf/hello.py`

2. `modules/ospf/module-02-neighbor-state-machine.md`
   - Question: How does a received Hello turn into `Init`, `2-Way`, or `Full`?
   - Lens: adjacency state + gate variables
   - Source: `src/protocol_in_code/ospf/neighbor.py`

3. `modules/ospf/module-03-dr-bdr-election.md`
   - Question: If several routers share one broadcast segment, how does the code pick DR and BDR?
   - Lens: candidate filtering + ranking
   - Source: `src/protocol_in_code/ospf/dr_election.py`

4. `modules/ospf/module-04-lsa-as-object.md`
   - Question: What does a Router-LSA have to contain before flood and SPF can use it?
   - Lens: object shape + version identity
   - Source: `src/protocol_in_code/ospf/lsa.py`

5. `modules/ospf/module-05-flooding-decides-where-lsa-goes.md`
   - Question: Once a newer LSA is received, where should it be forwarded next?
   - Lens: flood eligibility + outgoing interfaces
   - Source: `src/protocol_in_code/ospf/flooding.py`

6. `modules/ospf/module-06-lsdb-keeps-the-version.md`
   - Question: How does the LSDB decide whether a newly received Router-LSA replaces the old one?
   - Lens: area bucket + replace-or-ignore logic
   - Source: `src/protocol_in_code/ospf/lsdb.py`

7. `modules/ospf/module-07-spf-turns-lsdb-into-a-tree.md`
   - Question: What are the exact inputs to SPF, and what object does SPF return?
   - Lens: graph build + Dijkstra result
   - Source: `src/protocol_in_code/ospf/spf.py`

8. `modules/ospf/module-08-tree-becomes-routes.md`
   - Question: How does the shortest-path tree turn into actual reachable prefixes?
   - Lens: first hop recovery + route derivation
   - Source: `src/protocol_in_code/ospf/routing.py`

9. `modules/ospf/module-09-cost-picks-the-winner.md`
   - Question: If the same prefix appears more than once, which route wins?
   - Lens: route comparison + winner selection
   - Source: `src/protocol_in_code/ospf/cost.py`

10. `modules/ospf/module-10-topology-change-recomputes-the-rib.md`
    - Question: When a Router-LSA changes, which part of the route table has to be recomputed?
    - Lens: change trigger + route diff
    - Source: `src/protocol_in_code/ospf/recompute.py`

11. `modules/ospf/module-11-area-boundaries-rewrite-the-view.md`
    - Question: What changes when routes cross an area boundary through an ABR-like summary step?
    - Lens: summary generation + import rewrite
    - Source: `src/protocol_in_code/ospf/areas.py`

12. `modules/ospf/module-12-build-the-toy-ospf-speaker-loop.md`
    - Question: What does the smallest readable OSPF speaker look like when Hello, LSDB, SPF, and area summary are connected?
    - Lens: speaker object + event-shaped methods
    - Source: `src/protocol_in_code/ospf/speaker.py`

### DNS

1. `modules/dns/module-01-query-as-question-object.md`
   - Question: What is a DNS query made of, and when are two lookups the same lookup?
   - Lens: question identity + structural validation
   - Source: `src/protocol_in_code/dns/query.py`

2. `modules/dns/module-02-the-resolver-walks-down-the-tree.md`
   - Question: How does a resolver get from the root to an answer, one referral at a time?
   - Lens: bounded loop + longest-match descent
   - Source: `src/protocol_in_code/dns/walk.py`

3. `modules/dns/module-03-delegation-is-a-referral-not-an-answer.md`
   - Question: How does the resolver decide whether a response is an answer, a hand-off, or a dead end?
   - Lens: response classification + ordered branches
   - Source: `src/protocol_in_code/dns/referral.py`

4. `modules/dns/module-04-the-cache-answers-first.md`
   - Question: What exactly decides cache hit versus miss versus expired?
   - Lens: keyed state + read-time expiry
   - Source: `src/protocol_in_code/dns/cache.py`

5. `modules/dns/module-05-ttl-is-a-clock-not-a-config.md`
   - Question: What TTL does a client actually receive, and who removes an entry at zero?
   - Lens: time arithmetic + sweep function
   - Source: `src/protocol_in_code/dns/ttl.py`

6. `modules/dns/module-06-cname-restarts-the-question.md`
   - Question: How does asking for an A record end at one when the name is an alias?
   - Lens: name substitution + loop guards
   - Source: `src/protocol_in_code/dns/cname.py`

7. `modules/dns/module-07-failure-has-flavors.md`
   - Question: Why is NXDOMAIN an answer while SERVFAIL and timeout are reasons to retry?
   - Lens: failure classification + fallback loop
   - Source: `src/protocol_in_code/dns/failures.py`

8. `modules/dns/module-08-build-the-toy-resolver-loop.md`
   - Question: What does the smallest readable resolver look like when validation, cache, walk, and CNAME restart are connected?
   - Lens: pipeline object + decision trace
   - Source: `src/protocol_in_code/dns/resolver.py`

### TCP

1. `modules/tcp/module-01-a-segment-carries-state.md`
   - Question: What does a TCP segment carry, and what combination of flags and payload is nonsensical on its face?
   - Lens: object shape + structural validity
   - Source: `src/protocol_in_code/tcp/segment.py`

2. `modules/tcp/module-02-three-packets-to-say-hello.md`
   - Question: Why does establishing a connection take exactly three segments, and what state is each side in after each one?
   - Lens: state transition table + reply per step
   - Source: `src/protocol_in_code/tcp/handshake.py`

3. `modules/tcp/module-03-sequence-numbers-wrap-around.md`
   - Question: What does "before" mean once 32-bit sequence numbers wrap, and why is plain `<` the wrong tool?
   - Lens: modular arithmetic + signed-difference comparison
   - Source: `src/protocol_in_code/tcp/seqnum.py`

4. `modules/tcp/module-04-the-window-is-room-left.md`
   - Question: What is the receive window, really, and why is it never stored — only computed?
   - Lens: derived value + buffer occupancy
   - Source: `src/protocol_in_code/tcp/window.py`

5. `modules/tcp/module-05-the-timer-learns-the-network.md`
   - Question: How does TCP decide how long to wait before declaring loss, when the right answer changes every round trip?
   - Lens: feedback estimator + clamped timer
   - Source: `src/protocol_in_code/tcp/rto.py`

6. `modules/tcp/module-06-three-duplicates-mean-loss.md`
   - Question: How does a sender infer loss from ACKs alone, without waiting for a timer?
   - Lens: duplicate counter + threshold branch
   - Source: `src/protocol_in_code/tcp/fast_retransmit.py`

7. `modules/tcp/module-07-cwnd-is-just-a-variable.md`
   - Question: Read as code, is congestion control anything more than rules for moving one integer up or down?
   - Lens: two-variable update rules + phase branch
   - Source: `src/protocol_in_code/tcp/congestion.py`

8. `modules/tcp/module-08-out-of-order-is-not-lost.md`
   - Question: What happens to a segment that arrives ahead of expectation, and how does the receiver catch up in one step?
   - Lens: gap buffer + contiguous drain loop
   - Source: `src/protocol_in_code/tcp/reassembly.py`

9. `modules/tcp/module-09-goodbye-takes-four-packets.md`
   - Question: Why does closing take four segments and a wait, instead of ending when one side is done talking?
   - Lens: two-sided close state machine + arithmetic expiry
   - Source: `src/protocol_in_code/tcp/teardown.py`

10. `modules/tcp/module-10-rst-ends-everything-now.md`
    - Question: What does a RST-ended connection skip, and what decides whether a RST is allowed to end it?
    - Lens: unconditional exit + in-window gate
    - Source: `src/protocol_in_code/tcp/reset.py`

11. `modules/tcp/module-11-build-the-toy-tcp-loop.md`
    - Question: What does one endpoint's whole life look like when handshake, delivery, congestion, reset, and teardown share a single object?
    - Lens: endpoint object + trace of every decision
    - Source: `src/protocol_in_code/tcp/speaker.py`

### TLS

1. `modules/tls/module-01-hello-lists-everything-you-can-do.md`
   - Question: What is a ClientHello actually made of, and what makes one invalid before any negotiation starts?
   - Lens: capability declaration as a printable object
   - Source: `src/protocol_in_code/tls/messages.py`

2. `modules/tls/module-02-agreement-is-a-set-intersection.md`
   - Question: When client and server each bring an ordered list of what they support, whose order decides the pick?
   - Lens: set intersection + server preference order
   - Source: `src/protocol_in_code/tls/negotiate.py`

3. `modules/tls/module-03-keys-grow-on-a-schedule.md`
   - Question: Where does each TLS secret come from, and why can none of them be computed out of order?
   - Lens: derive chain + staged secrets
   - Source: `src/protocol_in_code/tls/key_schedule.py`

4. `modules/tls/module-04-trust-is-a-walk-up-the-chain.md`
   - Question: What turns a stack of certificates into a single yes/no answer, and in what order do the checks run?
   - Lens: leaf-to-root walk loop + trust store lookup
   - Source: `src/protocol_in_code/tls/chain.py`

5. `modules/tls/module-05-a-cert-is-for-a-name.md`
   - Question: What decides whether a trusted certificate is allowed to speak for the hostname you asked for?
   - Lens: exact and wildcard matching rules as ordered branches
   - Source: `src/protocol_in_code/tls/hostname.py`

6. `modules/tls/module-06-resumption-is-a-cache-hit.md`
   - Question: What does a session ticket let a client skip, and what decides whether a stored ticket is still good?
   - Lens: keyed store + read-time expiry (same shape as the DNS cache)
   - Source: `src/protocol_in_code/tls/resumption.py`

7. `modules/tls/module-07-the-record-layer-is-an-envelope.md`
   - Question: What does a record protect, what stays visible outside, and what does a bad tag tell you versus what it doesn't?
   - Lens: framing + integrity tag
   - Source: `src/protocol_in_code/tls/record.py`

8. `modules/tls/module-08-failure-is-a-typed-message.md`
   - Question: When a handshake fails, what exactly gets sent back, and who decides whether the connection ends?
   - Lens: typed alerts + verdict-to-alert mapping tables
   - Source: `src/protocol_in_code/tls/alert.py`

9. `modules/tls/module-09-build-the-toy-handshake-loop.md`
   - Question: What does a complete handshake look like when hello, negotiation, verification, keys, tickets, and one protected record share two functions?
   - Lens: integration driver + decision trace
   - Source: `src/protocol_in_code/tls/handshake_loop.py`

### HTTP/QUIC

This track spans two source packages: `src/protocol_in_code/http/` (sessions 01-07, 10)
and `src/protocol_in_code/quic/` (sessions 08-09). Modules and walkthroughs live in
`modules/http-quic/` and `examples/http-quic/`.

1. `modules/http-quic/module-01-a-request-is-parsed-text.md`
   - Question: Before any semantics or routing, what shape does raw HTTP text have to match, and what breaks it?
   - Lens: text splitting + shape validation
   - Source: `src/protocol_in_code/http/parse.py`

2. `modules/http-quic/module-02-headers-come-with-rules.md`
   - Question: What turns a flat list of name/value pairs into "valid" or "invalid," and who decides?
   - Lens: normalization + a visible dict of rules
   - Source: `src/protocol_in_code/http/headers.py`

3. `modules/http-quic/module-03-keep-alive-is-a-pool.md`
   - Question: How does a client decide between reusing an idle connection and opening a new one, and what makes an idle one stop being reusable?
   - Lens: keyed pool + read-time eviction
   - Source: `src/protocol_in_code/http/pool.py`

4. `modules/http-quic/module-04-cacheable-is-a-decision-tree.md`
   - Question: Should this response be stored, can a stored copy be reused right now, and does revalidation confirm nothing changed?
   - Lens: three ordered decision functions
   - Source: `src/protocol_in_code/http/caching.py`

5. `modules/http-quic/module-05-redirects-are-a-bounded-loop.md`
   - Question: What two mechanisms make redirect-following guaranteed to terminate, and what determines whether a POST survives the trip?
   - Lens: bounded loop + visited set + method rewrite rules
   - Source: `src/protocol_in_code/http/redirect.py`

6. `modules/http-quic/module-06-chunked-is-a-parser-state-machine.md`
   - Question: What single field tracks where the parser is in the size-line/data alternation, and what makes an error permanent?
   - Lens: explicit parser states + sticky terminals
   - Source: `src/protocol_in_code/http/chunked.py`

7. `modules/http-quic/module-07-streams-share-one-connection.md`
   - Question: What proves each HTTP/2 stream's state is tracked separately, and what makes the first frame on a stream special?
   - Lens: per-stream state dict + frame dispatch
   - Source: `src/protocol_in_code/http/h2_streams.py`

8. `modules/http-quic/module-08-quic-streams-dont-block-each-other.md`
   - Question: What, mechanically, keeps one stream's gap from ever touching another stream's delivery?
   - Lens: the TCP reassembly buffer shape, keyed per stream
   - Source: `src/protocol_in_code/quic/streams.py`

9. `modules/http-quic/module-09-flow-control-is-a-credit-balance.md`
   - Question: With flow control at two levels at once, what decides whether a send goes through, and what happens to each balance when the answer is no?
   - Lens: one credit-account shape used at two levels
   - Source: `src/protocol_in_code/quic/flow_control.py`

10. `modules/http-quic/module-10-build-the-toy-http-server-loop.md`
    - Question: What is the exact loop that wires parsing, header checks, and cache revalidation together, once per request, for as many requests as one connection carries?
    - Lens: server object + per-request pipeline + decision trace
    - Source: `src/protocol_in_code/http/server_loop.py`

## Planned Tracks

Session plans for candidate tracks are drafted in [`IDEAS.md`](IDEAS.md) with per-module
titles in the same naming style. Next candidates (not yet confirmed): Packet Parser,
RPKI, DHCP, RIP, NAT/conntrack, ARP/ND, Rate Limiter, Load Balancer, NTP,
Small State Machines (VRRP+BFD).

Candidate tracks beyond these (Packet Parser, RPKI, DHCP, RIP, NAT/conntrack, ARP/ND,
Rate Limiter, Load Balancer, NTP, Small State Machines) are also drafted in `IDEAS.md`.
This file only lists a track once its modules exist.
