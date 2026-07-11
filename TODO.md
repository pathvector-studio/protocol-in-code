# Protocol in Code 開発 TODO

トラック単位で進める。各トラックのセッション案（タイトル・Lens・Source）は `IDEAS.md`、
公開済みトラックの正典マップは `COURSE_MAP.md`。

## トラック実装キュー
- [x] DNS トラックの実装 (再帰的解決の関数チェーン、キャッシュルックアップおよびTTLロジック) — 2026-07-11 全8セッション完了
- [x] TCP トラックの実装 — 2026-07-11 全11セッション完了（src+modules+examples、walkthrough全86アサーション通過）
- [x] TLS トラックの実装 — 2026-07-11 全9セッション完了（walkthrough全61アサーション通過）
- [x] HTTP / QUIC トラックの実装 — 2026-07-11 全10セッション完了（http+quic 2パッケージ、walkthrough全73アサーション通過）
- [x] Packet Parser トラックの実装 — 2026-07-11 全5セッション完了（バイト列とビット演算の土台、pcapリーダーcapstone）
- [x] RPKI トラックの実装 — 2026-07-11 全5セッション完了（BGPトラック04-05の深掘り版、validator sweep capstone）
- [x] DHCP トラックの実装 — 2026-07-11 全6セッション完了（DORA、期限付きdict第4の再登場）
- [x] RIP トラックの実装 — 2026-07-11 全6セッション完了（OSPF対照実験、count-to-infinity再現）
- [x] NAT / conntrack トラックの実装 — 2026-07-11 全6セッション完了（2キー挿入、tick()のポートリークを検証中に発見・修正）
- [x] ARP/ND トラックの実装 — 2026-07-11 全4セッション完了（劣化するキャッシュ、spoofing防御）
- [x] QoS トラックの実装 — 2026-07-11 全5セッション完了（token/leaky対比、クラス木）
- [x] Load Balancer トラックの実装 — 2026-07-11 全6セッション完了（remap実測 0.80 vs 0.20）
- [x] NTP トラックの実装 — 2026-07-11 全4セッション完了（4タイムスタンプ算術、非対称の不可視性）
- [x] HA (VRRP+BFD) トラックの実装 — 2026-07-11 全4セッション完了（2時間スケールのフェイルオーバー）

## 次の候補トラック確定待ち
第1・第2世代は全て消化済み（14トラック / 116 modules）。次は `IDEAS.md` の**第3世代候補**
（ICMP/Traceroute → DNSSEC → TCP第2弾 → STP → STUN/ICE → IGMP → Same Shape=最終章）から確定して投入。

## その先の候補トラック（`IDEAS.md` にタイトルまで起こし済み）
Packet Parser / RPKI / DHCP / RIP / NAT-conntrack / ARP-ND / Rate Limiter / Load Balancer / NTP / Small State Machines (VRRP+BFD)
