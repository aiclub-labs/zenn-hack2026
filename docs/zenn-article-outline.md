# Zenn 記事 章立て — Dialogue Delta

提出物の一つ。Microsoft Agent Hackathon 2026 への応募エントリ記事 (Zenn の hack2026 tag)。

**ターゲット読者**: Azure / Semantic Kernel / GenAI でエンタープライズ業務適用を考える Eng + PM。
**長さ目標**: 8,000-12,000 字 (画像/コード含めて読了 15 分前後)。
**トーン**: 設計判断と trade-off を見せる。誇張なし、citation あり、コード断片入り。

## 章構成

### 0. TL;DR (200 字 + 図 1)
- 「自社 corpus を LLM の grounding 必須にしつつ、応答で立ち上がる暗黙知を Hearout → 形式知化 → corpus に還す」ループ
- アーキ図 1 枚 (Chat → Critic → Gap → Hearout → Formalize → Review → Corpus)

### 1. 解こうとした問題 (800 字)
- 暗黙知が個人/Slack/Teams に堆積 → 退職や異動でロスト
- 既存 GenAI は grounding なし or 出典提示なし
- Notion AI / Copilot の限界

### 2. アプローチの 3 軸 (1,500 字)
- **citation 必須**: 出典なしの応答を block
- **self-critic + delta detection**: LLM の自信度 + retrieval 距離で「知らない」を可視化
- **Hearout → Formalize**: gap を自動で 5W1H ヒアリングに変換、weight 算出後 review queue

### 3. 設計の trade-off (1,500 字)
- Why Semantic Kernel (group chat) over LangChain
- Why 12 Cosmos collections (vs single-table)
- Why citation enforcement at generation layer (not retrieval cutoff)
- Why critic を gpt-4o-mini に分離 (コスト + bias 排除)

### 4. 実装ハイライト (2,000 字)
- `app/api/turn.py` の retrieval ↔ generation 層分離 (P2-C1)
- Prompt injection 防御 (P2-C2): system / user separator + few-shot 拒否例
- 自己承認 (high-weight 自動 commit) と conflict resolution
- Trace context: `retrieval_ctx` で audit trail

### 5. 観測した挙動と驚き (1,500 字)
- 改善後 LLM が "知らない" と高 critic で defer → gap rate が低下 (= 設計成功)
- citation top-k の relevance 分布
- AI Search の semantic ranker 効果
- 「審査員もハルシネートできない」面白さ

### 6. コスト (1,000 字)
- PoC 実測 ¥1,491 (3日) → 推定 ¥14,000 (全期間)
- Enterprise 100 user 投影 ¥175,000/月 = ¥1,750/user/月
- 競合比較 (Notion AI / Copilot / ChatGPT Team)
- 未実装の cost 制御 (prompt cache / semantic cache)

### 7. デモ & リンク (300 字)
- 動画 (mp4 / youtube)
- 動く UI URL (web-chat)
- GitHub URL (aiclub-labs/zenn-hack2026)
- Team mention

### 8. 学び・残課題 (800 字)
- AOAI quota 申請 → PAYG への遅延ハマり
- AI Search Basic SLA / Standard 昇格判断
- Discord → Teams 移行は payload 差し替えのみ (cost-model §5)
- 次やるなら: prompt cache + semantic cache (30-40% 削減)
- Open question: 暗黙知の "本人しか知らない理由" をどこまで形式化すべきか

## 必須要素チェックリスト (Hackathon 提出 4 点との対応)

- [ ] 動画 URL (Shot 5/31)
- [ ] 動く App URL (web-chat 公開済)
- [ ] Markdown 記事 (この outline → 本文化)
- [ ] GitHub URL (現状 aiclub-labs/zenn-hack2026)

## 執筆フロー (5/31 night)

1. 0/1/7 を先に書く (構成と入口/出口)
2. 2/3 を書く (差別化の核)
3. 4/5 を書く (技術 meat)
4. 6/8 を書く (締め)
5. アーキ図 1 枚 (drawio → SVG)
6. コードスニペット 5-7 個 (api/turn.py, dispatcher.py, delta_detector.py)
7. Discord 着弾スクショ 4 枚
8. 投稿前 lint: 出典 URL、図 alt、長文段落分割
