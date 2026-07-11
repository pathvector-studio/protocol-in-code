# Protocol in Code — セッション案 (Generation Queue)

BGP (15) / OSPF (12) に続くトラックのセッション案。裏で走る記事生成の供給源。
命名スタイルは BGP/OSPF に合わせる: **宣言文タイトル**（プロトコルの事実をコードの言葉で言い切る）、
最終モジュールは恒例の **"Build the toy X loop"** で締める。
各モジュールは COURSE_MAP と同じ型: Question（タイトルがそのまま答える疑問）× Lens × Source。
ファイル名は `modules/<track>/module-NN-<slug>.md`、slug はタイトルの kebab-case。

進行状況: 第1・第2世代の全14トラック = **完了（2026-07-11 → COURSE_MAP.md へ移行）**
（DNS / TCP / TLS / HTTP-QUIC / Packet Parser / RPKI / DHCP / RIP / NAT / ARP / QoS / LB / NTP / HA）。
次のキューは下の「第3世代候補」（7トラック / 約35 modules）。

---

## Track: DNS — 8 modules【完了 2026-07-11】

`modules/dns/` に8本生成済み。正典は COURSE_MAP.md 参照（Source は
query.py / walk.py / referral.py / cache.py / ttl.py / cname.py / failures.py / resolver.py で確定）。

拡張候補（DNS第2弾として追加可能）: bailiwick 検証（毒入り回答をどこで弾くか）、DNSSEC の鍵→署名→DS 再帰検証。

## Track: TCP — 11 modules【完了 2026-07-11】

`modules/tcp/` に11本生成済み。正典は COURSE_MAP.md 参照（Source は
segment.py / handshake.py / seqnum.py / window.py / rto.py / fast_retransmit.py /
congestion.py / reassembly.py / teardown.py / reset.py / speaker.py で確定。
計画時の `speaker_loop.py` は BGP/OSPF に合わせ `speaker.py` に統一）。

## Track: TLS — 9 modules【完了 2026-07-11】

`modules/tls/` に9本生成済み。正典は COURSE_MAP.md 参照（Source は
messages.py / negotiate.py / key_schedule.py / chain.py / hostname.py /
resumption.py / record.py / alert.py / handshake_loop.py で確定）。
鍵導出とAEADはsha256ベースの代役（本物の暗号ではないとコード内に明記）。
resumption は DNS cache と同型であることをコード・文書の両方で相互参照済み。

## Track: HTTP/QUIC — 10 modules【完了 2026-07-11】

`modules/http-quic/` に10本生成済み（トラックは `http/` + `quic/` の2ソースパッケージ跨ぎ）。
正典は COURSE_MAP.md 参照（Source は parse.py / headers.py / pool.py / caching.py /
redirect.py / chunked.py / h2_streams.py / quic/streams.py / quic/flow_control.py /
server_loop.py で確定）。quic/streams.py は tcp/reassembly.py と「同じ形がストリーム単位で
再登場する」対比、pool/resumption 系は期限付き dict の再登場として相互参照済み。

---

## 新トラック候補（TODO 未記載、同スタイルでタイトルまで用意）

### Track: Packet Parser — 5 modules【完了 2026-07-11】

`modules/parser/` に5本生成済み。正典は COURSE_MAP.md 参照（Source は
ethernet.py / dispatch.py / ip.py / checksum.py / pcap_loop.py で確定）。
capstone は pcap 形式を自力パースし、magic number の二重解釈でバイトオーダーを検出する構成。

### Track: RPKI — 5 modules【完了 2026-07-11】

`modules/rpki/` に5本生成済み。正典は COURSE_MAP.md 参照（Source は
roa.py / covering.py / validate.py / policy.py / validator_loop.py で確定）。
BGPトラック Session 04-05 を相互参照する深掘り版。IPv4限定・署名/CA階層なしの正直なtoy。

### 第2世代 8トラック【全て完了 2026-07-11】

DHCP(6) / RIP(6) / NAT(6) / ARP-ND(4) / QoS(5) / Load Balancer(6) / NTP(4) / HA=VRRP+BFD(4)
= 計41 modules を生成済み。正典は COURSE_MAP.md 参照。計画時からの主な確定事項:
NAT の `tuple.py` 案は `five_tuple.py` に、RIP/HA の capstone は `speaker.py`/`failover_loop.py` に確定。
NAT tick() のポート返却リークを検証中に発見して修正（walkthrough でアサート済み）。


## 第3世代候補（2026-07-11起こし、全12トラック完了後のキュー）

### Track: ICMP / Traceroute — 5 modules（Packet Parser の続編、推し順1）

1. **An error is a packet about a packet** — ICMPエラーは元パケットの引用を運ぶ / `icmp/message.py`
2. **Unreachable has flavors** — net/host/port/frag-needed の分岐 / `icmp/unreachable.py`
3. **TTL is a hop budget** — 減算と時間切れ / `icmp/ttl.py`
4. **Time exceeded draws the map** — エラーを測定に転用する発明 / `icmp/probing.py`
5. **Build the toy traceroute loop** — TTL=1,2,3…の総集編 / `icmp/trace_loop.py`

### Track: DNSSEC — 5 modules（DNS第2弾、既存 dns/ トラックの直接続編、推し順2）

1. **A signature rides beside the record** — RRSIG は答えの隣に座る / `dnssec/rrsig.py`
2. **The key signs the key** — KSK/ZSK の二段構え / `dnssec/dnskey.py`
3. **DS links child to parent** — 親ゾーンに置く子の指紋 / `dnssec/ds.py`
4. **Validation walks up the tree** — 信頼の再帰（TLSの chain walk と対比） / `dnssec/chain.py`
5. **Build the toy validating resolver** — dns/resolver.py に検証を接ぐ総集編 / `dnssec/validator_loop.py`

### Track: TCP第2弾 (Operational TCP) — 6 modules（推し順3）

1. **TIME_WAIT is a promise with a price** — ポート枯渇の算術 / `tcp2/time_wait_cost.py`
2. **SYN cookies are stateless memory** — 状態をシーケンス番号に符号化する / `tcp2/syn_cookies.py`
3. **Nagle and delayed ACK deadlock** — 2つの善意が40msの遅延を作る相互作用シミュレーション / `tcp2/nagle_delack.py`
4. **Keepalive probes an idle line** — 沈黙の確認（NAT timeout との接続） / `tcp2/keepalive.py`
5. **The backlog is two queues** — SYNキューとacceptキューの分離 / `tcp2/backlog.py`
6. **Build the toy connection janitor** — 総集編 / `tcp2/janitor_loop.py`

### Track: STP — 5 modules（L2の空白を埋める）

1. **The root is the lowest ID** — 選出=比較関数、5回目の再登場 / `stp/root_election.py`
2. **Cost decides the path to root** — root path cost の累積 / `stp/path_cost.py`
3. **Ports have roles** — root/designated/blocked の割当 / `stp/port_roles.py`
4. **Blocking is how loops die** — BPDU比較とブロックの成立 / `stp/blocking.py`
5. **Build the toy spanning tree loop** — 総集編 / `stp/stp_loop.py`

### Track: STUN/ICE — 5 modules（NAT トラックの直接続編）

1. **STUN tells you your own address** — 外から見た自分の発見 / `ice/stun.py`
2. **NATs have personalities** — mapping挙動の分類（nat/ トラックと相互参照） / `ice/nat_behavior.py`
3. **Candidates are gathered, not chosen** — host/reflexive/relay の収集 / `ice/candidates.py`
4. **Pairs are checked in priority order** — チェックリストの優先度式 / `ice/checklist.py`
5. **Build the toy connectivity check loop** — 総集編 / `ice/ice_loop.py`

### Track: IGMP / Multicast — 4 modules

1. **Group membership is a set** — join/leave は集合演算 / `igmp/membership.py`
2. **Queries keep the set honest** — 定期クエリと期限（また期限付き状態） / `igmp/querier.py`
3. **Snooping reads someone else's mail** — L2スイッチがL3を盗み見る理由 / `igmp/snooping.py`
4. **Build the toy querier loop** — 総集編 / `igmp/querier_loop.py`

### Track: Same Shape, Different Protocol — 5 modules（全トラック完了後の**コース最終章**）

コースの差別化テーマ「同じコード構造の再登場」を正面から扱う総括トラック。
各モジュールが複数パッケージを import して同じ形を並べて見せる。

1. **The expiring dict, five times** — DNS cache / TLS ticket / DHCP lease / conntrack / QoS lazy refill / `meta/expiring_state.py`
2. **Election is a comparison function, five times** — BGP best path / OSPF DR / RIP better / VRRP / LB / `meta/election.py`
3. **Three states beat two** — RPKI verdict / BFD / ARP moods の三値設計 / `meta/tristate.py`
4. **Silence means failure, everywhere** — BFD / VRRP / keepalive / NAT timeout の沈黙推論 / `meta/silence.py`
5. **Every protocol ends in a loop** — 12個の toy loop の共通骨格を抽出する / `meta/the_loop.py`

推し順: ICMP → DNSSEC → TCP第2弾 → STP → STUN/ICE → IGMP → Same Shape（最終章、全トラック後）。

## 供給計画メモ（2026-07-11更新）

- 在庫: 公開済み **14トラック / 116 modules**（BGP15 OSPF12 DNS8 TCP11 TLS9 HTTP-QUIC10 Parser5 RPKI5 DHCP6 RIP6 NAT6 ARP4 QoS5 LB6 NTP4 HA4）。ブログ公開ペース（EN 2本/日想定）で**約2カ月分**。
- 残キュー: 第3世代 **7トラック / 約35 modules** ≈ さらに1カ月強。
- 型の遵守: 各トラック最終回は "Build the toy X loop"。タイトルは「プロトコルの事実をコードの言葉で言い切る」宣言文。
- 差別化の軸: **同じコード構造が別プロトコルで再登場する**ことを本文で明示的に相互参照する。確立済みの系譜: 期限付きdict（DNS→TLS→NAT→DHCP）、選出比較関数（BGP→OSPF→RIP→VRRP→LB）、沈黙=障害（BFD/VRRP/NAT timeout）、劣化するキャッシュ（ARP）。最終章 Same Shape トラックがこれらを総括する。
