# Protocol in Code — セッション案 (Generation Queue)

BGP (15) / OSPF (12) に続くトラックのセッション案。裏で走る記事生成の供給源。
命名スタイルは BGP/OSPF に合わせる: **宣言文タイトル**（プロトコルの事実をコードの言葉で言い切る）、
最終モジュールは恒例の **"Build the toy X loop"** で締める。
各モジュールは COURSE_MAP と同じ型: Question（タイトルがそのまま答える疑問）× Lens × Source。
ファイル名は `modules/<track>/module-NN-<slug>.md`、slug はタイトルの kebab-case。

進行状況: **全3世代 23トラック / 151 modules 完了（第1・2世代 2026-07-11、第3世代 2026-07-12 → COURSE_MAP.md へ移行）**。
キューは空。次世代の候補はこのファイルに同スタイル（宣言文タイトル + toy loop締め + Question/Lens/Source）で起こしてから生成に回す。

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


## 第3世代 7トラック【全て完了 2026-07-12】

ICMP/Traceroute(5) / DNSSEC(5) / TCP第2弾(6) / STP(5) / STUN-ICE(5) / IGMP(4) /
Same Shape, Different Protocol(5・コース最終章) = 計35 modules を生成済み。正典は COURSE_MAP.md 参照。
計画からの主な確定事項: 最終章 meta/ トラックは22個のcapstoneを横断importする比較コードとして実装
（期限付きdict×5並走、選出比較×5、三値×4、沈黙タイムスケール実測 150ms〜7,800,000ms、
dns+tcpの2ループ並走実行）。DNSSECの期限切れは BOGUS_RECORD_SIG に折り畳まれる実挙動で確定。


## 供給計画メモ（2026-07-12更新）

- 在庫: 公開済み **23トラック / 151 modules**（全3世代完了、コースは Same Shape 最終章で一区切り）。
  ブログ公開ペース（EN 2本/日想定）で**約2.5カ月分**。protocol-lab 側の在庫と合わせ数カ月分を確保。
- 残キュー: 空。次世代候補の起こし方はこのファイル先頭の型に従う。ネタの方向性メモ:
  protocol-lab の IDEAS.md（テーマA〜J、約60本）に未消化の中級化候補が多数（IPv6系、
  WebSocket/gRPC、NetFlow、Kerberos/OAuth系のトークン検証など）。
- 型の遵守: 各トラック最終回は "Build the toy X loop"。タイトルは「プロトコルの事実をコードの言葉で言い切る」宣言文。
- 差別化の軸: **同じコード構造が別プロトコルで再登場する**こと。確立済みの系譜は最終章 meta/ トラックが
  コードとして総括済み（期限付きdict×5、選出比較×5、三値×4、沈黙=障害×4、そして22個のtoy loop）。
  新トラックを足すときは必ずどの系譜に接続するかを計画段階で決める。
