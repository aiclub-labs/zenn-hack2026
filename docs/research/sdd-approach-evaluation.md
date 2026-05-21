# Claude Code 文脈での Spec-Driven Development アプローチ評価 (2026-05)

## TL;DR
- Kiro 流 SDD (requirements → design → tasks の 3 段 + steering) は 2026-05 時点でも主流の 1 つ。Claude Code 上では gotalab/cc-sdd が事実上の標準実装で、Opus 4.7 と相性良好。
- 競合の GitHub Spec Kit は `constitution.md` で「上位原則」を切り出し、複数機能を `specs/<feature>/` 群で並べる構造。Kiro の steering と思想は近いが、`constitution` 概念は Kiro に無く Spec Kit の方が新しい。
- 本ハッカソンの多機能構成では Kiro 維持で OK。ただし「上位 overview」を `.kiro/steering/product.md` に集約し、umbrella spec は作らず feature spec を並列に切るのが現状ベストプラクティス。

## 1. Kiro SDD 現状 (2025-2026)
- 発祥は AWS Kiro IDE (2025)。Requirements (EARS 記法) → Design → Tasks の 3 フェーズ、各フェーズで人間承認、`product.md / tech.md / structure.md` を steering として常時参照する設計は 2026 も維持。
- Claude Code 移植は **gotalab/cc-sdd** が中心 (旧 claude-code-spec、現 cc-sdd; 8 エージェント対応、Claude Code/Codex stable)。2026 リリースで Opus 4.5/4.7、GPT-5.2、Gemini 3 Flash に追従。`/kiro:steering`, `/kiro:spec-init`, `/kiro:spec-requirements`, `/kiro:spec-design`, `/kiro:spec-tasks`, `/kiro:spec-impl`, `/kiro:validate-*` の構成は我々のセットと一致。
- Martin Fowler (Böckeler) の SDD 分類では Kiro は **"spec-anchored"** (spec が contract、code が source of truth)。Tessl の "spec-as-source" とは別系統。Kiro は AI に「要件の推測」を許さない staged approval が強み。

## 2. 代替アプローチ比較

| アプローチ | 上位 spec の有無 | フェーズ区切り | 多機能プロジェクト対応 | Claude Code 統合度 |
|---|---|---|---|---|
| **Kiro / cc-sdd** | steering (`product/tech/structure.md`) | Req → Design → Tasks → Impl (人間承認) | feature 別 `.kiro/specs/<f>/` 並列 + steering 共通 | ◎ slash command + skill 両対応 |
| **GitHub Spec Kit** | `constitution.md` (非交渉原則) | Constitution → Specify → Plan → Tasks → Implement | `specs/<feature>/` を並べる、memory archive | ○ slash command (Claude Code / Copilot / Gemini CLI 等) |
| **Claude 公式 plan mode + skills** | CLAUDE.md / skills SKILL.md | plan → edit (2 段) | 構造化無し、ユーザー裁量 | ◎ ネイティブ (Shift+Tab×2) |
| **Aider architect/editor** | 無し | architect → editor 2 段 | 弱い (リポジトリ単位) | △ 別 CLI |
| **Tessl (spec-as-source)** | spec 自体が source | spec → 再生成 | spec ファイル単位 | △ 別 IDE |
| **BMAD / Superpowers** | brainstorm → plan skill | brainstorm → plan → TDD → review | skill chain で柔軟 | ○ Claude Code skill chain |

要確認: Aider architect mode の 2026 最新仕様 (本文未確認)。

## 3. 上位 overview ドキュメントの位置付け
- **Kiro**: 上位 vision は `.kiro/steering/product.md`、各 feature の入力は `requirements.md` 冒頭の Project Description に集約する設計のまま (1 feature = 1 spec が単位)。別の `overview.md` を切るパターンは公式仕様には無い。
- **Spec Kit**: 明示的に `constitution.md` という上位文書を導入。Kiro の `product.md` と機能的に重なるが、「coding agent が毎タスク前に必ず読む non-negotiable rules」という運用ルールが明文化されている点で Kiro より厳格。
- **示唆**: Kiro を使い続けるなら `steering/product.md` を Spec Kit の constitution 相当として運用 (非交渉原則を箇条書きで明記) するのが 2026 時点のベストプラクティス。

## 4. 多機能プロジェクト時の構成パターン
- 公式 Kiro / cc-sdd の標準は **「steering で束ねる + feature spec を並列に切る」** 一択。umbrella spec / メタ spec パターンは公式ドキュメントには未登場 (要確認: コミュニティの非公式パターンは Issue 91 等で metadata 拡張議論あり)。
- Spec Kit も同様に `specs/<feature>/` を並べる構造。「features を main project memory に archive して横断調整」という運用は導入されたが、umbrella spec 文書は無い。
- ハッカソン (複数機能をデモする提出物) の場合:
  1. `steering/product.md` に「製品ビジョン + どの機能を含むか」のリストを書く (= 軽量 umbrella の代替)
  2. 各機能を `.kiro/specs/{feature-a, feature-b, ...}/` に並列に切る
  3. 機能間依存は各 `design.md` の「Related Specs」セクションでクロスリンク
- umbrella spec を別途切るのは公式仕様逸脱になるため非推奨。どうしても必要なら `steering/roadmap.md` (custom steering) で代用。

## 5. Claude Code 文脈での推奨

**結論: Kiro / cc-sdd を維持。修正は軽微で OK。**

- 活きる点: Opus 4.7 の 1M context + xhigh effort は staged approval と相性が良く、`design.md` を一気に詰めても文脈落ちしない。`/kiro:validate-*` は subagent 化に向き、メイン context を消費しない。skill 化された各コマンドは plan mode と直交。
- 摩擦点:
  - `requirements.md` の Project Description が長くなりすぎると Opus でも要件抜けが出る → 上位 vision を steering/product.md に追い出す運用で解消。
  - フェーズ承認を毎回手動でやると速度低下 → 信頼できる feature は `-y` 高速化、リスク高い design 段は必ず人間レビュー。
  - 多機能プロジェクトで steering が肥大化 → `steering-custom` で feature 群ごとに分割。
- 切替候補との比較:
  - Spec Kit 切替の利得は `constitution.md` だけ。代用容易なので切替コスト見合わず。
  - 公式 plan mode 単独は spec の永続化 (リポジトリ contract 化) が弱く、ハッカソンのような複数日跨ぎワークでは Kiro 優位。

軽微な改善案: `steering/product.md` を constitution 風 (non-negotiable rules を箇条書き) に書き直す。`.kiro/specs/<f>/research.md` は Kiro 公式仕様外なので、cc-sdd 最新版で `validate-gap` の出力が research.md に出るか要確認。

## 6. 出典
- [Kiro Specs (公式)](https://kiro.dev/docs/specs/) — Req/Design/Tasks 3 段の公式定義 (本文確認: 検索抜粋経由)
- [Kiro Best Practices](https://kiro.dev/docs/specs/best-practices/) — 要確認: WebFetch 制限により本文未読
- [gotalab/cc-sdd README](https://github.com/gotalab/cc-sdd) — Claude Code 移植版の公式リポ。コマンド一覧と 2026 リリースノート (検索抜粋経由)
- [cc-sdd spec-driven.md](https://github.com/gotalab/cc-sdd/blob/main/docs/guides/spec-driven.md) — フェーズ詳細 (要確認: 本文未読)
- [GitHub Spec Kit](https://github.com/github/spec-kit) — constitution → specify → plan → tasks (検索抜粋経由)
- [Spec Kit spec-driven.md](https://github.com/github/spec-kit/blob/main/spec-driven.md) — 要確認: 本文未読
- [Martin Fowler / Böckeler: Kiro, spec-kit, Tessl](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html) — spec-first / spec-anchored / spec-as-source 分類 (検索抜粋経由)
- [MarkTechPost: 9 Best AI Tools for SDD 2026](https://www.marktechpost.com/2026/05/08/9-best-ai-tools-for-spec-driven-development-in-2026-kiro-bmad-gsd-and-more-compare/) — 2026-05 時点のツール俯瞰 (要確認: 本文未読)
- [Claude Opus 4.7 best practices (Anthropic)](https://claude.com/blog/best-practices-for-using-claude-opus-4-7-with-claude-code) — 1M context, xhigh effort (検索抜粋経由)
- [Kiro: Opus 4.7 now available](https://kiro.dev/blog/opus-4-7/) — Kiro × Opus 4.7 (検索抜粋経由)
- [Devpost Learning Hackathon: SDD with Claude Code](https://learn-ai.devpost.com/) — Anthropic 公認ハッカソンでも SDD が推奨 (検索抜粋経由)
- [cc-sdd Issue #91: custom metadata in spec.json](https://github.com/gotalab/cc-sdd/issues/91) — multi-repo spec 管理議論 (要確認: 本文未読)
