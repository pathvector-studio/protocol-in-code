# Protocol in Code — セッション案 (Generation Queue)

BGP (15) / OSPF (12) に続くトラックのセッション案。裏で走る記事生成の供給源。
命名スタイルは BGP/OSPF に合わせる: **宣言文タイトル**（プロトコルの事実をコードの言葉で言い切る）、
最終モジュールは恒例の **"Build the toy X loop"** で締める。
各モジュールは COURSE_MAP と同じ型: Question（タイトルがそのまま答える疑問）× Lens × Source。
ファイル名は `modules/<track>/module-NN-<slug>.md`、slug はタイトルの kebab-case。

進行状況: DNS / TCP / TLS / HTTP-QUIC / Packet Parser / RPKI = **完了（2026-07-11 → COURSE_MAP.md へ移行）**。
次は下の残り候補から確定して投入（推し順: DHCP → RIP）。

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

### Track: DHCP — 6 modules

1. **Discovery is shouting into the dark** — ブロードキャストと DORA の始まり / `dhcp/discover.py`
2. **An offer is a proposal with a deadline** — lease 候補の提示 / `dhcp/offer.py`
3. **The pool hands out what's free** — アドレス割当関数 / `dhcp/pool.py`
4. **A lease is a dict with an expiry** — DNS cache と同型だと気づく回 / `dhcp/leases.py`
5. **Renewal happens before the end** — T1/T2 タイマー / `dhcp/renewal.py`
6. **Build the toy DHCP server loop** — 総集編 / `dhcp/server_loop.py`

### Track: RIP / Distance Vector — 6 modules（OSPF=link state の対照実験）

1. **A route is a rumor with a distance** — 距離ベクトルの入力構造 / `rip/route.py`
2. **Bellman-Ford is a for loop** — 更新式をそのまま書く / `rip/update.py`
3. **Sixteen means unreachable** — 無限の定義 / `rip/infinity.py`
4. **Rumors can circle back** — count-to-infinity をテストで再現 / `rip/count_to_infinity.py`
5. **Don't tell me what I told you** — split horizon は送信フィルタ / `rip/split_horizon.py`
6. **Build the toy RIP loop** — link state との思想比較で締め / `rip/speaker_loop.py`

### Track: NAT / conntrack — 6 modules

1. **A connection is a 5-tuple** — 対応表のキー設計 / `nat/tuple.py`
2. **Translation is a rewrite function** — SNAT/DNAT の書換 / `nat/rewrite.py`
3. **The reply finds its way back** — 逆引きテーブル / `nat/reverse.py`
4. **Ports are a shared resource** — 割当と衝突処理 / `nat/ports.py`
5. **State expires, again** — 期限付き dict 第3回（DNS/DHCP と同型） / `nat/timeout.py`
6. **Build the toy NAT box loop** — 総集編 / `nat/nat_loop.py`

### Track: ARP/ND — 4 modules

1. **The cache has moods** — INCOMPLETE/REACHABLE/STALE の状態付き dict / `arp/cache.py`
2. **Packets wait for answers** — 解決待ちキュー / `arp/pending.py`
3. **Anyone can answer** — gratuitous ARP と上書き（攻撃面に接続） / `arp/gratuitous.py`
4. **Build the toy ARP responder loop** — 総集編 / `arp/responder_loop.py`

### Track: Rate Limiter / QoS — 5 modules（protocol-lab Lab 28 の中級版）

1. **A token bucket is two variables** — 残高 + 最終補充時刻 / `qos/token_bucket.py`
2. **Refill is lazy** — アクセス時にまとめて補充する技法 / `qos/refill.py`
3. **Leaky and token are cousins** — 2方式の比較 / `qos/leaky_bucket.py`
4. **Classes form a tree** — 階層化シェーピング / `qos/classes.py`
5. **Build the toy shaper loop** — 総集編 / `qos/shaper_loop.py`

### Track: Load Balancer — 6 modules（protocol-lab Lab 33 の中級版）

1. **Round robin is one index** — 最小の分散 / `lb/round_robin.py`
2. **Least connections is a counter** — 状態を見る分散 / `lb/least_conn.py`
3. **Hashing keeps you on the same server** — session affinity / `lb/hash.py`
4. **The ring survives a server change** — consistent hashing の二分探索 / `lb/ring.py`
5. **Health is a state machine** — up/down 判定とフラップ抑制 / `lb/health.py`
6. **Build the toy load balancer loop** — 総集編 / `lb/lb_loop.py`

### Track: NTP — 4 modules

1. **Four timestamps, two unknowns** — offset/delay の算術 / `ntp/offset.py`
2. **Stratum is depth in a tree** — 時刻の系譜 / `ntp/stratum.py`
3. **Symmetry is an assumption** — 往復対称性という核心の仮定 / `ntp/asymmetry.py`
4. **Build the toy NTP client loop** — 総集編 / `ntp/client_loop.py`

### Track: Small State Machines (VRRP + BFD) — 4 modules

1. **The highest priority speaks** — VRRP master 選出は比較関数 / `ha/vrrp_election.py`
2. **Silence means failure** — advertisement タイムアウト / `ha/vrrp_timeout.py`
3. **Three states, both directions** — BFD の 3-way state machine / `ha/bfd.py`
4. **Build the toy failover loop** — 総集編 / `ha/failover_loop.py`

---

## 供給計画メモ

- 在庫数: 確定 DNS 8 + 案 TCP 11 / TLS 9 / HTTP-QUIC 10 = **38**、新トラック候補 **51** → 合計 **約90 modules**。既存 BGP/OSPF 27 と合わせ、日次ドリップ1本換算で**約4カ月分**。
- 投入順の推し: DNS（生成中）→ TCP → Packet Parser（他トラックの土台になる）→ RPKI（BGP資産と接続）→ TLS → HTTP/QUIC → 残り。
- 型の遵守: 各トラック最終回は "Build the toy X loop"。タイトルは「プロトコルの事実をコードの言葉で言い切る」宣言文。
- 差別化の軸: **同じコード構造が別プロトコルで再登場する**ことを本文で明示的に相互参照する（期限付き dict = DNS cache / DHCP lease / conntrack、状態付き dict = ARP cache、比較関数による選出 = BGP best path / VRRP election）。
