# Observability — App Insights KQL クエリ集

> 作成: 2026-05-28 / 用途: framework-review.md gap #3 (Fairness proxy / T3) + 継続評価ループ (T4)。
> 関連: `app/util/telemetry.py` (`emit_metric`), `app/api/reviews.py` (`review.decision`), `app/util/cost.py` (`aggregate_aoai_tokens_daily`).

すべて Azure Portal の Application Insights → Logs から実行可能。`customMetrics` テーブルは emit_metric が出力する OpenTelemetry counter の集約先。

---

## 1. Fairness proxy — sector × reviewer × decision rate (T3)

### 1.1 reviewer 別 approve/reject 比率（自己承認率 proxy）

```kusto
customMetrics
| where name == "review.decision"
| where timestamp > ago(7d)
| extend reviewer_id = tostring(customDimensions["reviewer_id"]),
         sector       = tostring(customDimensions["sector"]),
         unit         = tostring(customDimensions["unit"]),
         decision     = tostring(customDimensions["decision"])
| summarize approve = countif(decision == "approve"),
            edit    = countif(decision == "edit"),
            reject  = countif(decision == "reject")
            by reviewer_id, sector, unit
| extend total = approve + edit + reject
| extend approve_rate = todouble(approve) / todouble(total),
         reject_rate  = todouble(reject)  / todouble(total)
| project reviewer_id, sector, unit, approve, edit, reject, total, approve_rate, reject_rate
| order by total desc
```

> `countif()` 版に統一 (Issue #34): `evaluate pivot()` は `edit` 等の空 decision を持つテナントで列ごと欠落させるため、空集合 safe な集計に変更。

**運用**: `approve_rate > 0.85` かつ `total >= 10` の reviewer はバイアス候補 (Req 9.9 の self-approval warning 30% は別軸：自分提出→自分承認の self-loop rate)。

### 1.2 sector × decision 比率（domain bias proxy）

```kusto
customMetrics
| where name == "review.decision"
| where timestamp > ago(30d)
| extend sector = tostring(customDimensions["sector"]),
         decision = tostring(customDimensions["decision"])
| summarize approve = countif(decision == "approve"),
            edit    = countif(decision == "edit"),
            reject  = countif(decision == "reject")
            by sector
```

**運用**: 同一 schema を持つ複数 sector で reject_rate が 2 倍以上乖離 → schema 偏り or 提供者層偏りの仮説検証へ。

### 1.3 24h SLA breach 検知 (Req 9.7)

```kusto
customMetrics
| where name == "review.decision"
| where timestamp > ago(1d)
| extend ticket_id = tostring(customDimensions["ticket_id"])
| summarize last_decision = max(timestamp) by ticket_id
| where last_decision < ago(24h)
```

---

## 2. Continuous iteration loop — weekly customMetrics workbook (T4)

> AWS GenAI Lens "Continuous iteration" phase に対応。Workbook 1 枚で週次トレンドを可視化。

### 2.1 AOAI トークン日次（コスト + sustainability proxy）

```kusto
customMetrics
| where name == "aoai.token.total"
| where timestamp > ago(14d)
| extend agent = tostring(customDimensions["agent"]),
         model = tostring(customDimensions["model"])
| summarize tokens = sum(value) by bin(timestamp, 1d), agent, model
| render timechart
```

### 2.2 Truth Judgment verdict 分布の推移

```kusto
customMetrics
| where name == "tj.verdict"
| where timestamp > ago(14d)
| extend verdict = tostring(customDimensions["verdict"]),
         sector  = tostring(customDimensions["sector"])
| summarize count() by bin(timestamp, 1d), verdict
| render columnchart with (kind=stacked)
```

**観察軸**: `novel` 比率の推移 = 暗黙知の新規捕捉ペース。低下したら schema 飽和の兆候。

### 2.3 Hearout 完走 / skip / expire 率

```kusto
customMetrics
| where name == "hearout.outcome"
| where timestamp > ago(14d)
| extend outcome = tostring(customDimensions["outcome"])
| summarize count() by bin(timestamp, 1d), outcome
| evaluate pivot(outcome, sum(count_))
```

**観察軸**: `skipped` が 60% を超え続けると Persona B の介入耐性が限界。介入頻度 throttling を検討。

### 2.4 Self-critic スコア分布

```kusto
customMetrics
| where name == "self_critic.score"
| where timestamp > ago(14d)
| summarize avg(value), percentile(value, 50), percentile(value, 90) by bin(timestamp, 1d)
| render timechart
```

### 2.5 Review 中央値時間（SLO トラッキング）

```kusto
customMetrics
| where name == "review.duration_sec"
| where timestamp > ago(14d)
| summarize p50 = percentile(value, 50),
            p90 = percentile(value, 90)
  by bin(timestamp, 1d)
| render timechart
```

---

## 3. Alert ルール推奨

| Metric | 条件 | 通知先 |
|---|---|---|
| `review.decision` reject_rate (sector 単位) | 1 週間で 2 倍以上の急増 | Persona A (Admin) |
| `hearout.outcome` skipped 比率 | 7d rolling > 60% | dev チーム |
| `aoai.token.total` 日次 | $200 予算の forecast 80% 到達 | オペレータ |
| `tj.verdict` novel 比率 | 7d rolling < 5% | Persona A (Admin) |

---

## 4. Workbook 配置

Phase 2 で `infra/modules/observability.bicep` を追加し本クエリを Workbook テンプレートとしてデプロイ予定。ハッカソンスコープでは本書を README から link することで「continuous iteration の設計は完了、Workbook 自動配置は post-hack」と表明する。

---

**End of observability-kql.md** — framework-review.md gap #3 (Fairness proxy) と AWS GenAI Lens Continuous Iteration phase を解消。
