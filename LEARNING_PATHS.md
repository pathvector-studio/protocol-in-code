# Learning Paths

The course has 23 tracks / 151 sessions. Nobody should read them in publication order.
This page groups the tracks by genre, then gives goal-based roadmaps — including where
to start if you are new, and how this course connects to its beginner sibling,
[Protocol Lab](https://github.com/pathvector-studio/protocol-lab).

日本語: 23トラック/151セッションを「公開順」に読む必要はありません。このページは
トラックをジャンルで束ね、目的別の推奨ルート（初心者の入口、入門コース Protocol Lab
との接続を含む）を示します。

## Genres

| Genre | Tracks (recommended internal order) | What it teaches |
|---|---|---|
| Foundations 基礎 | Packet Parser | Bytes, offsets, bit masks — how anything on the wire is read at all |
| Routing 経路制御 | BGP → OSPF → RIP → RPKI | How routers decide paths: policy, link state, distance vector, and origin trust |
| The local segment L2とローカル | ARP → STP → IGMP | What happens before IP: resolution, loops, and multicast on one wire |
| Transport トランスポート | TCP → TCP2 → QoS | Reliable delivery, what operating it costs, and pacing traffic |
| Names & trust 名前と信頼 | DNS → DNSSEC → TLS | Finding things by name and deciding whether to believe the answer |
| The web path Webの配管 | HTTP/QUIC → LB | From parsed request to multiplexed streams to picking a backend |
| Addresses & reachability アドレスと到達性 | DHCP → NAT → ICE → ICMP | Getting an address, sharing one, punching through, and reading the error mail |
| Time & liveness 時刻と生死 | NTP → HA (VRRP+BFD) | Agreeing what time it is and inferring death from silence |
| Finale 総括 | Same Shape, Different Protocol | The five code structures the whole course secretly repeats |

Every genre path ends well positioned for the **Same Shape** track — read it last,
whichever route you take. It is the course's closing argument.

日本語: どのルートで来ても、最後は **Same Shape** トラック（コース全体で繰り返された
コード構造の総括）で締めるのが推奨です。

## Roadmaps by goal

### 1. Complete beginner 初めてネットワークを学ぶ

Start with **Protocol Lab**, not this course. Protocol Lab is hands-on-first: you run
two routers, capture packets, and see protocols behave before reading them as code.

1. Protocol Lab Labs 01–12 (BGP → RPKI → DNS → TCP → TLS → HTTP → QUIC → end-to-end)
2. Come back here: **Packet Parser** (5) — the byte-level ground floor
3. **DNS** (8) — the friendliest track: loops, caches, and failure flavors
4. **TCP** (11) — state machines, timers, recovery
5. **Same Shape** (5) — you have now seen every recurring structure once

日本語: 完全な初心者はまず Protocol Lab（手を動かす入門編）のLab 01〜12へ。その後この
コースに戻り、Packet Parser → DNS → TCP → Same Shape の順が最短の背骨です。

### 2. Web engineer Webエンジニア

You call APIs all day; this route explains everything between `fetch()` and the server.

DNS (8) → TCP (11) → TLS (9) → HTTP/QUIC (10) → LB (6) → TCP2 (6) → Same Shape (5)
— 55 sessions. After this route: you can explain a slow request end to end
(resolution, handshake, HoL blocking, LB pick, TIME_WAIT pileup).

### 3. Infra / network engineer インフラ・ネットワークエンジニア

The router-room route. Packet Parser (5) → ARP (4) → DHCP (6) → ICMP (5) → BGP (15)
→ OSPF (12) → RIP (6) → RPKI (5) → STP (5) → HA (4) → Same Shape (5) — 72 sessions.
Pairs naturally with Protocol Lab's containerlab exercises for each protocol.

### 4. Security-minded セキュリティ志向

Trust chains and the places they break. Packet Parser (5) → TLS (9) → DNSSEC (5)
→ RPKI (5) → ARP (4, the unauthenticated cache) → NAT (6) → ICE (5) → Same Shape (5)
— 44 sessions. Recurring theme: what is signed, what is merely believed, and which
third state (NOT_FOUND / INSECURE / STALE) keeps the system honest.

### 5. SRE / operations SRE・運用

Why production behaves like that. TCP (11) → TCP2 (6) → LB (6) → QoS (5) → NTP (4)
→ HA (4) → ICMP (5) → NAT (6) → IGMP (4) → Same Shape (5) — 56 sessions.
Recurring theme: timeouts, budgets, and silence-means-failure at every timescale.

## Protocol Lab ↔ Protocol in Code

The two courses are independent but rhyme. If a Lab made you curious, this table says
which track reads the same protocol as code (and vice versa: run the Lab after the
track to watch your mental model hold up on real packets).

日本語: Labで動かして面白かったプロトコルは、対応するトラックでコードとして読めます。
逆にトラックを読んだ後にLabを動かすと、理解が実パケットで裏取りできます。

| Theme | Protocol Lab (hands-on) | Protocol in Code (read the logic) |
|---|---|---|
| BGP | Labs 01–03, 31 (anycast) | bgp (15) |
| RPKI | Lab 04 | rpki (5) |
| DNS | Labs 05–06, 13–14, 41–42 | dns (8), dnssec (5) |
| TCP | Labs 07–08, 30 (congestion), 37 (MSS) | tcp (11), tcp2 (6) |
| TLS | Labs 09, 15 (mTLS), 17 (DANE) | tls (9) |
| HTTP / QUIC | Labs 10–11, 27 | http-quic (10) |
| DHCP | Lab 22 | dhcp (6) |
| ARP / ND | Labs 23–24 | arp (4) |
| NAT | Labs 20, 40 | nat (6), ice (5) |
| OSPF | Lab 34 | ospf (12) |
| BFD / failover | Lab 35 | ha (4) |
| Load balancing | Labs 32–33, 41 | lb (6) |
| QoS | Lab 28 | qos (5) |
| Multicast | Lab 29 | igmp (4) |
| Traceroute / ICMP | Labs 19, 25 (PMTUD) | icmp (5) |
| Packet reading | (tcpdump throughout) | parser (5) |
| Spanning tree | — (course gap: no Lab yet) | stp (5) |
| Time sync | — (course gap: no Lab yet) | ntp (4) |
| Distance vector | — (contrast track) | rip (6) |

Course gaps in that table (STP, NTP) are natural candidates for future Protocol Lab
batches.

## How to read any single track

Whatever route you pick, each track works the same way — the rhythm is:

1. Read the module doc's Core Question.
2. Read the source file it names (they are 30–200 lines, deliberately).
3. Run the walkthrough: `PYTHONPATH=src python3 examples/<track>/session_NN_walkthrough.py`
4. Answer the Failure Questions from the source, not from memory.
5. Finish the track with its "Build the toy X loop" capstone.

日本語: どのトラックも「問いを読む → 30〜200行のソースを読む → walkthrough を実行 →
Failure Questions に（記憶でなく）コードで答える → capstone の toy loop で締める」の
同じリズムで進みます。
