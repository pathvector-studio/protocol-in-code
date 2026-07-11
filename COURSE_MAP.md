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
| Packet Parser | Published | 5 | headers as offset promises, bit masks, and one-line checksums |
| RPKI | Published | 5 | ROAs, prefix math, and the tri-state verdict under BGP policy |
| DHCP | Published | 6 | broadcast discovery, offer deadlines, and lease expiry as shared state |
| RIP | Published | 6 | distance-vector rumor propagation and its count-to-infinity failure mode |
| NAT | Published | 6 | 5-tuple identity, stateless rewrite, and port allocation under expiry |
| ARP/ND | Published | 4 | an unauthenticated cache that degrades trust instead of just expiring |
| QoS | Published | 5 | token buckets, lazy refill, and hierarchical class trees as shaping math |
| Load Balancer | Published | 6 | picking strategies, consistent hashing, and health as a state machine |
| NTP | Published | 4 | offset and delay solved from four timestamps under an assumption of symmetry |
| HA (VRRP+BFD) | Published | 4 | two-timescale failure detection racing toward the same failover decision |
| (7 candidate tracks) | Idea pool | ~35 | see `IDEAS.md` (第3世代) |

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

### Packet Parser

The byte-level foundation the other tracks deliberately skip.

1. `modules/parser/module-01-bytes-have-a-shape.md`
   - Question: How does the parser know which bytes are which field, without reading anything but position?
   - Lens: named offset constants + explicit slices
   - Source: `src/protocol_in_code/parser/ethernet.py`

2. `modules/parser/module-02-peel-one-layer-find-the-next.md`
   - Question: How does a number like 0x0800 or 6 turn into a decision about which parser to call?
   - Lens: literal number-to-name tables + lookup
   - Source: `src/protocol_in_code/parser/dispatch.py`

3. `modules/parser/module-03-bits-dont-align-to-bytes.md`
   - Question: How does the parser pull an exact field out of the middle of a byte?
   - Lens: shifts and masks with named bit constants
   - Source: `src/protocol_in_code/parser/ip.py`

4. `modules/parser/module-04-the-checksum-is-arithmetic-not-magic.md`
   - Question: What does 16-bit addition with end-around carry do, and why does a valid header sum to all-ones?
   - Lens: pure integer arithmetic, no dataclasses (like tcp/seqnum.py)
   - Source: `src/protocol_in_code/parser/checksum.py`

5. `modules/parser/module-05-build-the-toy-pcap-reader.md`
   - Question: What does it take to turn a pcap byte stream into the layered read the last four sessions built?
   - Lens: byte-order detection from the magic + record loop + per-packet layer walk
   - Source: `src/protocol_in_code/parser/pcap_loop.py`

### RPKI

The deeper standalone treatment of what BGP sessions 04-05 introduced; verdicts here
feed the policy shapes the learner saw there.

1. `modules/rpki/module-01-a-roa-is-a-permission-slip.md`
   - Question: What is a ROA, stripped of everything except the three facts it asserts?
   - Lens: three-field object + structural validation
   - Source: `src/protocol_in_code/rpki/roa.py`

2. `modules/rpki/module-02-covering-is-prefix-math.md`
   - Question: "Does this ROA say anything about this announcement?" is really two questions — what are they?
   - Lens: range containment and specificity as two separate functions
   - Source: `src/protocol_in_code/rpki/covering.py`

3. `modules/rpki/module-03-three-verdicts-not-two.md`
   - Question: Why three verdicts instead of a bool, and what separates the two flavors of invalid?
   - Lens: tri-state outcome + reason strings (deepens bgp/validation.py)
   - Source: `src/protocol_in_code/rpki/validate.py`

4. `modules/rpki/module-04-policy-decides-what-a-verdict-means.md`
   - Question: A verdict is a fact about the world — what does a router actually do with it, and who decides?
   - Lens: two policy booleans + verdict-to-action mapping (deepens bgp/policy.py)
   - Source: `src/protocol_in_code/rpki/policy.py`

5. `modules/rpki/module-05-build-the-toy-validator-loop.md`
   - Question: What does a validator's whole job look like when load, check, and table sweep share one object?
   - Lens: validator object + decision trace + verdict counting
   - Source: `src/protocol_in_code/rpki/validator_loop.py`

### DHCP

1. `modules/dhcp/module-01-discovery-is-shouting-into-the-dark.md`
   - Question: A DHCP client has no IP address yet — how does a message even get sent, and what does that fact do to the shape of the message itself?
   - Lens: broadcast as absence, not a value
   - Source: `src/protocol_in_code/dhcp/discover.py`

2. `modules/dhcp/module-02-an-offer-is-a-proposal-with-a-deadline.md`
   - Question: How long does a server wait on an unconfirmed offer, and how does it learn — without hearing directly from the client — that it lost?
   - Lens: deadline computed from made_at, echo as implicit decline
   - Source: `src/protocol_in_code/dhcp/offer.py`

3. `modules/dhcp/module-03-the-pool-hands-out-whats-free.md`
   - Question: How does a server pick the next free address from a /24, and avoid double-handing an address while an offer is still pending?
   - Lens: linear scan, two skip conditions (allocated vs on-hold)
   - Source: `src/protocol_in_code/dhcp/pool.py`

4. `modules/dhcp/module-04-a-lease-is-a-dict-with-an-expiry.md`
   - Question: Why is the code managing a DHCP lease table line-for-line identical to the code managing three other unrelated expiring stores this course has already built?
   - Lens: keyed state + read-time expiry (fourth appearance of the shape)
   - Source: `src/protocol_in_code/dhcp/leases.py`

5. `modules/dhcp/module-05-renewal-happens-before-the-end.md`
   - Question: Why does a client start asking for a new lease long before the old one expires, and who is it allowed to ask at each point in that countdown?
   - Lens: ordered condition branches (T1/T2/expiry, all >=)
   - Source: `src/protocol_in_code/dhcp/renewal.py`

6. `modules/dhcp/module-06-build-the-toy-dhcp-server-loop.md`
   - Question: What does the server actually check, and in what order, to make DORA's four messages come out right every time — including when two servers answer the same DISCOVER?
   - Lens: dispatch-then-delegate wiring, validate-first
   - Source: `src/protocol_in_code/dhcp/server_loop.py`

### RIP

1. `modules/rip/module-01-a-route-is-a-rumor-with-a-distance.md`
   - Question: A RipRoute is one neighbor's claim about hop count — what does it mean to trust a number like that, and what can the code check before you do?
   - Lens: hearsay record, no ground truth to check against
   - Source: `src/protocol_in_code/rip/route.py`

2. `modules/rip/module-02-bellman-ford-is-a-for-loop.md`
   - Question: What does it mean to run Bellman-Ford when all you have is a single pass over one neighbor's (prefix, metric) pairs?
   - Lens: single-pass relax, add-then-compare, same-source override
   - Source: `src/protocol_in_code/rip/update.py`

3. `modules/rip/module-03-sixteen-means-unreachable.md`
   - Question: Why is RIP's "unreachable" value 16 — not 255, not a billion — and what does picking a small number actually buy?
   - Lens: small ceiling as deliberate short fuse (>= boundary)
   - Source: `src/protocol_in_code/rip/infinity.py`

4. `modules/rip/module-04-rumors-can-circle-back.md`
   - Question: Why does a router that just lost a route end up believing its own rumor came back from a neighbor, and how many rounds does that belief take to burn out?
   - Lens: unfiltered mutual re-advertisement, round-by-round climb
   - Source: `src/protocol_in_code/rip/count_to_infinity.py`

5. `modules/rip/module-05-dont-tell-me-what-i-told-you.md`
   - Question: If the cure for count-to-infinity isn't smarter math, what is it, and where exactly does it run?
   - Lens: send-side filter, one field checked (next_hop)
   - Source: `src/protocol_in_code/rip/split_horizon.py`

6. `modules/rip/module-06-build-the-toy-rip-loop.md`
   - Question: What does the smallest readable RIP speaker look like when table, neighbors, outbound filter, and Bellman-Ford pass are wired into a round-robin convergence loop?
   - Lens: two-phase advertise/receive wiring, gossip vs shared-map contrast
   - Source: `src/protocol_in_code/rip/speaker.py`

### NAT

1. `modules/nat/module-01-a-connection-is-a-5-tuple.md`
   - Question: What identifies a connection to the kernel, and does the reply direction require anything beyond swapping two fields of that same identity?
   - Lens: identity as hashable key, not narrative
   - Source: `src/protocol_in_code/nat/five_tuple.py`

2. `modules/nat/module-02-translation-is-a-rewrite-function.md`
   - Question: When a router performs NAT, does it mutate the packet in place, or produce a new packet and let the old one go?
   - Lens: substitution, not mutation (frozen dataclasses)
   - Source: `src/protocol_in_code/nat/rewrite.py`

3. `modules/nat/module-03-the-reply-finds-its-way-back.md`
   - Question: When a reply arrives from the internet, how does the router already know where it belongs, and when was that decision actually made?
   - Lens: reply key pre-computed at insert time
   - Source: `src/protocol_in_code/nat/table.py`

4. `modules/nat/module-04-ports-are-a-shared-resource.md`
   - Question: How does the NAT box hand out a port no other flow is using, and what happens the moment the pool runs out?
   - Lens: linear-scan allocator with wraparound
   - Source: `src/protocol_in_code/nat/ports.py`

5. `modules/nat/module-05-state-expires-again.md`
   - Question: With no close signal from the network, what decides a conntrack entry is dead, and why does that take 10x longer for TCP than UDP?
   - Lens: stamp-and-compare expiry (fourth appearance)
   - Source: `src/protocol_in_code/nat/timeout.py`

6. `modules/nat/module-06-build-the-toy-nat-box-loop.md`
   - Question: What does a packet's full round trip through tuple, rewrite, table, ports, and clock look like wired into one box?
   - Lens: capstone wiring, no new logic
   - Source: `src/protocol_in_code/nat/nat_loop.py`

### ARP/ND

1. `modules/arp/module-01-the-cache-has-moods.md`
   - Question: When an ARP mapping outlives its freshness window, does it disappear, or just get less trusted?
   - Lens: three-state degrade, not delete (vs. DNS binary expiry)
   - Source: `src/protocol_in_code/arp/cache.py`

2. `modules/arp/module-02-packets-wait-for-answers.md`
   - Question: While an IP address is still unresolved, where does the packet that wanted to go there actually sit?
   - Lens: per-IP FIFO queue, drop-oldest on overflow
   - Source: `src/protocol_in_code/arp/pending.py`

3. `modules/arp/module-03-anyone-can-answer.md`
   - Question: With no authentication in ARP, what decides whether the cache believes an unsolicited announcement?
   - Lens: policy gate on unsolicited overwrite only
   - Source: `src/protocol_in_code/arp/gratuitous.py`

4. `modules/arp/module-04-build-the-toy-arp-responder-loop.md`
   - Question: What does one host's whole ARP life — sending, queuing, answering, gleaning — look like wired into a single object?
   - Lens: capstone wiring + unconditional gleaning
   - Source: `src/protocol_in_code/arp/responder_loop.py`

### QoS

1. `modules/qos/module-01-a-token-bucket-is-two-variables.md`
   - Question: What decides whether a request is allowed or throttled, with no queue, no timer, and no scheduler?
   - Lens: balance + lazy self-refill (vs. QUIC's externally-granted credit)
   - Source: `src/protocol_in_code/qos/token_bucket.py`

2. `modules/qos/module-02-refill-is-lazy.md`
   - Question: With no background clock ticking, when does a token bucket's balance actually get updated?
   - Lens: pure scalar math, settled on read (cf. dns/cache.py expiry check)
   - Source: `src/protocol_in_code/qos/refill.py`

3. `modules/qos/module-03-leaky-and-token-are-cousins.md`
   - Question: Same two variables, same lazy-settlement trick — why does an identical burst pass a token bucket but overflow a leaky bucket?
   - Lens: mirrored signs (add vs. subtract, floor vs. ceiling)
   - Source: `src/protocol_in_code/qos/leaky_bucket.py`

4. `modules/qos/module-04-classes-form-a-tree.md`
   - Question: What has to be true of a class tree before hierarchical borrowing math is trustworthy, and how much can a class actually borrow on paper?
   - Lens: three independent validation passes + static ancestor walk
   - Source: `src/protocol_in_code/qos/classes.py`

5. `modules/qos/module-05-build-the-toy-shaper-loop.md`
   - Question: What does it take to wire four standalone mechanisms into something that classifies a packet and decides its fate, keeping one class's exhaustion isolated from another's?
   - Lens: wiring, not new logic (one bucket per class name)
   - Source: `src/protocol_in_code/qos/shaper_loop.py`

### Load Balancer

1. `modules/lb/module-01-round-robin-is-one-index.md`
   - Question: How do you spread requests evenly across backends when you're willing to know nothing else about them?
   - Lens: single wrapping integer (blind ring walk)
   - Source: `src/protocol_in_code/lb/round_robin.py`

2. `modules/lb/module-02-least-connections-is-a-counter.md`
   - Question: If you track one number per backend, what does it buy you that round robin's blind index can't?
   - Lens: per-backend counter + deterministic tiebreak
   - Source: `src/protocol_in_code/lb/least_conn.py`

3. `modules/lb/module-03-hashing-keeps-you-on-the-same-server.md`
   - Question: How do you guarantee the same client lands on the same backend with no state at all, and what does that cost when the backend list changes?
   - Lens: stateless modulo fold (ends on unsolved problem)
   - Source: `src/protocol_in_code/lb/hash_pick.py`

4. `modules/lb/module-04-the-ring-survives-a-server-change.md`
   - Question: What has to change about the fold so only the keys that truly need to move actually move?
   - Lens: shared circle, binary search (removes len(backends) from the fold)
   - Source: `src/protocol_in_code/lb/ring.py`

5. `modules/lb/module-05-health-is-a-state-machine.md`
   - Question: What turns a stream of probe results into a routing decision, and why is going down fast and coming back slow the same design?
   - Lens: asymmetric thresholds (fail-fast, recover-slow)
   - Source: `src/protocol_in_code/lb/health.py`

6. `modules/lb/module-06-build-the-toy-load-balancer-loop.md`
   - Question: What does the smallest object look like that filters a live request through health before handing it to whichever picking strategy is configured?
   - Lens: health filter before strategy dispatch, always
   - Source: `src/protocol_in_code/lb/lb_loop.py`

### NTP

1. `modules/ntp/module-01-four-timestamps-two-unknowns.md`
   - Question: An NTP exchange hands back four timestamps — what can actually be solved for from just those four numbers, and what has to be assumed to get there?
   - Lens: derive offset/delay from two equations, not memorized formulas
   - Source: `src/protocol_in_code/ntp/offset.py`

2. `modules/ntp/module-02-stratum-is-depth-in-a-tree.md`
   - Question: What does an NTP server's advertised stratum number actually count, and why does a client prefer a lower one even at the cost of a longer round trip?
   - Lens: hop count, not quality score (like RIP metric)
   - Source: `src/protocol_in_code/ntp/stratum.py`

3. `modules/ntp/module-03-symmetry-is-an-assumption.md`
   - Question: When outbound and return delay are unequal, exactly how wrong does the reported offset get — and can the protocol ever detect it?
   - Lens: undetectable asymmetry error (half the delay gap)
   - Source: `src/protocol_in_code/ntp/asymmetry.py`

4. `modules/ntp/module-04-build-the-toy-ntp-client-loop.md`
   - Question: Given several exchanges with a server, how does a client decide which sample to trust and apply its correction without a dangerous jump?
   - Lens: filter by min-delay, then clamp (slew, not step)
   - Source: `src/protocol_in_code/ntp/client_loop.py`

### HA (VRRP+BFD)

1. `modules/ha/module-01-the-highest-priority-speaks.md`
   - Question: If several routers share one virtual IP, how does the code decide which one gets to be master?
   - Lens: max() over (priority, ip) tuple, tiebreak built-in
   - Source: `src/protocol_in_code/ha/vrrp_election.py`

2. `modules/ha/module-02-silence-means-failure.md`
   - Question: A VRRP backup never asks "are you alive?" — so how does it correctly infer the master is gone?
   - Lens: keyed timestamp + read-time expiry (>= boundary)
   - Source: `src/protocol_in_code/ha/vrrp_timeout.py`

3. `modules/ha/module-03-three-states-both-directions.md`
   - Question: How does a three-state machine reach mutual agreement that "the session is up" without a central decision-maker?
   - Lens: ordered condition branches, graduated up / immediate down
   - Source: `src/protocol_in_code/ha/bfd.py`

4. `modules/ha/module-04-build-the-toy-failover-loop.md`
   - Question: What does it actually look like when a millisecond-scale detector (BFD) and a seconds-scale detector (VRRP) are wired to watch the same failure on the same pair of routers?
   - Lens: two-timescale race, fast detector then fallback safety net
   - Source: `src/protocol_in_code/ha/failover_loop.py`

## Planned Tracks

Session plans for candidate tracks are drafted in [`IDEAS.md`](IDEAS.md) with per-module
titles in the same naming style. Next candidates (not yet confirmed, third-generation
queue): ICMP/Traceroute, DNSSEC, TCP第2弾 (Operational TCP), STP, STUN/ICE, IGMP,
Same Shape Different Protocol (course finale).

Candidate tracks beyond these are also drafted in `IDEAS.md`.
This file only lists a track once its modules exist.
