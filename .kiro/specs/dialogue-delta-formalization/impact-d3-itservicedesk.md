# D3: IT サービスデスク / SRE — ビジネスインパクト・ブリーフ

対象: Microsoft Agent Hackathon Japan 2026 デモ用ピッチ素材
作成日: 2026-05-27
対象市場: 日本国内 中堅〜大企業の社内 IT / SRE 部隊

---

## 1. 典型顧客像

| 項目 | 想定 |
|---|---|
| 業種 | 金融 / 製造 / 流通 / 通信 / 公共系インフラ (24/7 稼働が前提の事業) |
| 売上 | 1,000 億円 〜 数兆円 (東証プライム上場相当) |
| 情シス + SRE 人員 | 50〜300 名 (うち L2/L3 オンコール対応者 10〜40 名) |
| 運営構造 | 一次受付 (L1, 多くは社内ヘルプデスク or 委託 BPO) → L2 アプリ/インフラ → L3 ベテラン SRE / ベンダー の三層 |
| インシデント件数 | 月 数百〜数千 (うち P1/P2 重大は数件〜数十件) |
| 痛み | (a) L3 のベテランが定年 / 転職で抜けると初動が遅延、(b) 同種障害の再発、(c) オンコール疲弊による離職 |

出典: 調査対象は東証上場企業相当 4,500 社・有効回答 981 社という JUAS 企業 IT 動向調査 2025 のスコープが上記レンジを代表 ([JUAS 企業 IT 動向調査 2025 プレス](https://juas.or.jp/cms/media/2025/02/it25_2.pdf))。

---

## 2. 主要 KPI ベンチマーク

| KPI | 中央値 / 代表値 | レンジ | 出典 |
|---|---|---|---|
| インシデント MTTR (全業界 平均) | 8.85 業務時間 | 0.6h 〜 27.5h | [MetricNet via Motadata](https://www.motadata.com/blog/mean-time-to-resolution) |
| MTTR (重大インシデント, 高成熟チーム) | < 1h | 15min〜4h | [Palo Alto Cyberpedia / AlertOps](https://www.paloaltonetworks.com/cyberpedia/mean-time-to-repair-mttr) |
| MTTR (製造業 IT) | 48〜72h | — | [Motadata](https://www.motadata.com/blog/mean-time-to-resolution) |
| 一次解決率 (FCR, IT サービスデスク) | 74% (MetricNet) / 69% (SQM 2024) | 41〜94% | [SQM 2024 Benchmark](https://www.sqmgroup.com/resources/library/blog/call-center-fcr-benchmark-2024-results-by-industry), [MetricNet via HDI](https://www.thinkhdi.com/~/media/HDICorp/Files/Library-Archive/Insider%20Articles/mean-time-to-resolve.pdf) |
| エンジニア バーンアウト率 | 約 65% | — | [Runframe State of Incident Mgmt 2026](https://runframe.io/blog/state-of-incident-management-2025) |
| オンコール対応 5 件超/30 日 | 46% の SRE | — | 同上 |
| アラートのうち真に行動が必要 | 約 3% (週 2,000 アラート中) | — | 同上 |
| 1 時間あたりダウンタイムコスト (中堅〜大企業) | 90%超が **$300K/h 超** | $100K〜$5M+/h | [ITIC 2024 Hourly Cost of Downtime](https://itic-corp.com/itic-2024-hourly-cost-of-downtime-report/) |
| 大企業 (>1,000 名) で $1M〜$5M+/h | 41% | — | 同上 |
| Fortune 500 級 平均 | $500K〜$1M/h | 金融・医療は $5M+/h | [Gatling/Gartner 引用](https://gatling.io/blog/the-cost-of-downtime) |
| DORA 2024 — Elite の障害復旧 | < 1h | Low は数日〜1週 | [DORA 2024 (RedMonk まとめ)](https://redmonk.com/rstephens/2024/11/26/dora2024/) |

注: DORA 2024 では「AI ツールは低レベル作業を加速するが lead time / change failure rate には統計的有意な改善をまだ示せていない」と報告。我々のような **対話中の暗黙知抽出** はこの空白を埋める位置取り。

---

## 3. ¥ 効果計算式 (transparent)

### 前提パラメータ (1 社想定)

| パラメータ | 値 | 根拠 |
|---|---|---|
| P1/P2 インシデント年間件数 | 60 件 | 大企業 ITIC レンジ中位 |
| 平均ダウンタイム (現行) | 4.0h / 件 | 業界 MTTR 中央 8.85h を 24/7 系で半減と仮定 |
| ダウンタイム機会損失単価 | ¥3,000 万 / h ≒ $200K/h | ITIC 2024 中堅〜大企業ボトム帯 (保守) |
| L2/L3 平均人件費 (FTE 込) | ¥1,200 万 / 年 = ¥6,000/h | [SRE 中堅 700-1,000 万円 (xnetwork)](https://www.xnetwork.jp/contents/sre-annualincome) + 福利厚生・間接費 1.4 倍 |
| オンコール対応者離職率 | 15% / 年 | バーンアウト 65% × 顕在化係数を保守見積 |
| 1 名離職時の補填コスト | ¥1,500 万 | 採用 + ランプアップ 6-9 ヶ月の機会損失 |

### シナリオ A (保守: 効果半分が顕在化)

| 効果 | 算出 | 年間 ¥ |
|---|---|---|
| ダウンタイム削減 (MTTR -15%) | 60 件 × 4h × 0.15 × ¥3,000 万/h | ¥10.8 億 …※ ただしこのうち「我々のソリューション寄与」を 10% と仮置 | **¥1.08 億** |
| 一次解決率改善 (FCR +5pt → L2 エスカレ -7%) 工数削減 | 月 500 件 × 12 × 0.07 × 2h × ¥6,000 | **¥504 万** |
| 再発防止 (再発インシデント -20%, 全体の 15% が再発と仮定) | 60 × 0.15 × 0.20 × (4h × ¥3,000 万/h) | **¥2,160 万** |
| 離職抑制 (離職率 15% → 12%, 30 名母数) | 30 × 0.03 × ¥1,500 万 | **¥1,350 万** |
| **小計 (保守)** | | **約 ¥1.4 億 / 年** |

### シナリオ B (楽観: 寄与率 25%, MTTR -30%)

| 効果 | 算出 | 年間 ¥ |
|---|---|---|
| ダウンタイム削減 (寄与 25% × MTTR -30%) | 60 × 4h × 0.30 × 0.25 × ¥3,000 万 | **¥5.4 億** |
| FCR +10pt | 月 500 × 12 × 0.14 × 2h × ¥6,000 | **¥1,008 万** |
| 再発 -50% | 60 × 0.15 × 0.5 × 4h × ¥3,000 万 | **¥5,400 万** |
| 離職 15% → 9% | 30 × 0.06 × ¥1,500 万 | **¥2,700 万** |
| **小計 (楽観)** | | **約 ¥6.3 億 / 年** |

→ **「障害コスト ¥1 億規模顧客で ¥3,000-5,000 万 / 年」は保守シナリオの離職+再発+FCR 分 (約 ¥4,000 万) と一致**。ダウンタイム削減を含めれば ¥1 億超の余地あり。**前提の寄与率 10-25% が議論の核**。

---

## 4. 競合 / 既存ソリューション

| 製品 | アプローチ | 我々との差分 |
|---|---|---|
| [PagerDuty Copilot / SRE Agent](https://www.pagerduty.com/blog/product/product-launch-2025-h2/) | インシデント発生時の triage / Slack 上の post-incident draft / Splunk・Dynatrace ログ参照 | **事後** (発生〜終息) の自動化。**暗黙知の事前/対話中抽出はカバー外** |
| ServiceNow Now Assist | ITSM チケットの優先度判定・要約・ナレッジ生成 | チケット形式の構造化データが起点。会話そのものは扱わない |
| [Atlassian Rovo](https://www.atlassian.com/collections/service/ai) | 既存ドキュメント・チケットから runbook / PIR ドラフト生成 | **既に書かれているもの**を再利用。書かれていないベテランの暗黙知は対象外 |
| [Datadog Bits AI SRE](https://www.datadoghq.com/blog/bits-ai-sre/) | Slack 会話 + タイムラインから postmortem 草案 | postmortem (事後) 中心。"切分け順序" の知識化は副産物 |

**差別化ポイント**: 上記は全て **「インシデント発生後の自動化」**。我々は **「ベテランと若手が日常会話している瞬間に暗黙知を 5W1H 構造化する」** という Hearout / Delta Detector / Truth Judgment の組み合わせで、**インシデント発生前にナレッジ資産化** する。これは Google SRE Book が指摘する「experience and intuition are not repeatable, objective, or transferable」([sre.google](https://sre.google/sre-book/eliminating-toil/)) という根本問題へのアプローチ。

---

## 5. 暗黙知の典型例 (現場でドキュメント化されない知識)

| カテゴリ | 例 |
|---|---|
| 切分け順序 | 「DB スロークエリ疑いの時は先に X テーブルの統計情報を見る (理由: 過去に index 統計が壊れた)」 |
| 仮説選択 | 「金曜夜のレイテンシスパイクは大抵 batch job との競合、まず cron を疑う」 |
| ログ着眼点 | 「app log の WARN は読まなくていい。FATAL の 3 秒前の DEBUG 行を読む」 |
| アラート真偽判定 | 「アラート 2,000 件のうち本当に行動必要は 3%」([State of Incident Management 2026](https://runframe.io/blog/state-of-incident-management-2025))。どれが本物かは暦・直近デプロイ・季節要因の組合せ判断 |
| 過去類似事例 | 「2 年前の祝日明けに似た現象あり、結局 DNS TTL だった」 |

これらは Google SRE Book でも「tribal knowledge」「quirks and tedious bits」として明示的に課題視されている ([sre.google/workbook/eliminating-toil](https://sre.google/workbook/eliminating-toil/))。

---

## 6. C4 (社会課題性) 補強材料

- **経産省 2030 IT 人材不足試算 = 最大 79 万人** ([経済産業省 商務情報政策局 資料](https://www.meti.go.jp/shingikai/economy/daiyoji_sangyo_skill/pdf/001_06_00.pdf), [NTT Com 解説](https://www.ntt.com/bizon/d/00491.html)) — 数を増やせない以上、一人あたり生産性 / 知識継承効率を上げる以外に道がない
- **IPA DX 動向 2024**: DX を推進する人材が「大幅に不足」と回答した企業 **62.1%** (初の過半数突破) ([IPA プレス 20240627](https://www.ipa.go.jp/pressrelease/2024/press20240627.html), [IPA 報告書 PDF](https://www.ipa.go.jp/digital/chousa/discussion-paper/f55m8k00000039kf-att/dx-talent-shortage.pdf))
- **2025 年の崖**: レガシー保守人材の引退と若手への継承失敗が DX 全体の足を引っ張るというストーリー ([経産省 DX レポート関連](https://www.meti.go.jp/shingikai/economy/daiyoji_sangyo_skill/pdf/001_06_00.pdf))
- **エンジニア バーンアウト 65%** ([Runframe 2026](https://runframe.io/blog/state-of-incident-management-2025)) — 「人を増やせない × 残った人が辞めていく」という二重苦

これにより「単なる効率化 SaaS」ではなく **「日本社会の構造課題に対する解」** という framing が成立。

---

## 7. 主要出典 (URL 一覧)

1. [ITIC 2024 Hourly Cost of Downtime Report](https://itic-corp.com/itic-2024-hourly-cost-of-downtime-report/) — ダウンタイムコスト
2. [DORA 2024 Report (RedMonk summary)](https://redmonk.com/rstephens/2024/11/26/dora2024/) — MTTR / Change Failure Rate / AI 効果
3. [MetricNet MTTR Benchmark (via HDI)](https://www.thinkhdi.com/~/media/HDICorp/Files/Library-Archive/Insider%20Articles/mean-time-to-resolve.pdf) — MTTR / FCR
4. [SQM Group FCR Benchmark 2024](https://www.sqmgroup.com/resources/library/blog/call-center-fcr-benchmark-2024-results-by-industry) — 一次解決率
5. [Google SRE Workbook: Eliminating Toil](https://sre.google/workbook/eliminating-toil/) — tribal knowledge / 50% rule
6. [State of Incident Management 2026 (Runframe)](https://runframe.io/blog/state-of-incident-management-2025) — バーンアウト 65% / アラート 3% / Toil +30%
7. [経済産業省 IT 人材試算 (商務情報政策局)](https://www.meti.go.jp/shingikai/economy/daiyoji_sangyo_skill/pdf/001_06_00.pdf) — 2030 年 79 万人不足
8. [IPA DX 動向 2024 プレス](https://www.ipa.go.jp/pressrelease/2024/press20240627.html) / [報告書 PDF](https://www.ipa.go.jp/digital/chousa/discussion-paper/f55m8k00000039kf-att/dx-talent-shortage.pdf) — DX 人材不足 62.1%
9. [JUAS 企業 IT 動向調査 2025](https://juas.or.jp/cms/media/2025/02/it25_2.pdf) — 日本大企業 IT 部門スコープ
10. [PagerDuty H2 2025 Release](https://www.pagerduty.com/blog/product/product-launch-2025-h2/) — 競合: SRE Agent / Scribe Agent
11. [Datadog Bits AI SRE](https://www.datadoghq.com/blog/bits-ai-sre/) — 競合: 自動 postmortem
12. [Atlassian Rovo for Service](https://www.atlassian.com/collections/service/ai) — 競合: runbook 生成
13. [日本 SRE 年収 (X Network)](https://www.xnetwork.jp/contents/sre-annualincome) — 人件費見積根拠

---

## 8. この数字を本気で出すなら追加検証すべき点

1. **寄与率 (10〜25%) の実証** — 「我々の暗黙知抽出が MTTR 短縮にどれくらい効くか」は本質的に未検証。PoC で同種チーム 2 つを比較するパイロットが必要。仮説では (a) 切分け第一手の正答率、(b) L1 → L2 エスカレ削減、を中間 KPI に置く
2. **日本特化のダウンタイムコスト** — ITIC は global 数字。日本企業の機会損失は B2B SLA 補償 / 顧客解約への影響度が欧米と異なる可能性。JUAS や日本の障害事例 (例: みずほ・全銀ネット) からの実額検証が必要
3. **暗黙知のうち AI で抽出可能な割合** — Google SRE Book は「intuition は transferable ではない」と書いている。すべてが言語化可能とは限らず、5W1H 構造化で取れる範囲を定量化する必要 (pilot で「ベテラン 1h 対話 → 抽出 N 件 → 後日障害で実際に役立った件数」を測る)
4. **再発率の現状ベースライン** — 「再発 -50%」は再発率の現状値を知らないと意味を持たない。15% と仮置したが顧客毎に 5〜40% の幅。導入前 3 ヶ月のベースライン測定が前提
5. **離職抑制の因果** — 「暗黙知が共有されると新人の不安が減って離職率が下がる」は仮説。実証には介入後 12 ヶ月以上の追跡が必要。短期デモでは「主観的なオンコール負荷」アンケートで proxy する
