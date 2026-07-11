# Protocol in Code 開発 TODO

トラック単位で進める。各トラックのセッション案（タイトル・Lens・Source）は `IDEAS.md`、
公開済みトラックの正典マップは `COURSE_MAP.md`。

## トラック実装キュー
- [x] DNS トラックの実装 (再帰的解決の関数チェーン、キャッシュルックアップおよびTTLロジック) — 2026-07-11 全8セッション完了
- [x] TCP トラックの実装 — 2026-07-11 全11セッション完了（src+modules+examples、walkthrough全86アサーション通過）
- [x] TLS トラックの実装 — 2026-07-11 全9セッション完了（walkthrough全61アサーション通過）
- [x] HTTP / QUIC トラックの実装 — 2026-07-11 全10セッション完了（http+quic 2パッケージ、walkthrough全73アサーション通過）

## 次の候補トラック確定待ち
`IDEAS.md` の候補（Packet Parser, RPKI, DHCP, RIP, NAT-conntrack, ARP-ND, Rate Limiter, Load Balancer, NTP, Small State Machines）から次を確定して生成キューへ。推し順: Packet Parser → RPKI（既存BGPトラックと接続）。

## その先の候補トラック（`IDEAS.md` にタイトルまで起こし済み）
Packet Parser / RPKI / DHCP / RIP / NAT-conntrack / ARP-ND / Rate Limiter / Load Balancer / NTP / Small State Machines (VRRP+BFD)
