# Zenn 投稿セットアップ — AI Club account + GitHub Integration

## 状態

- ✅ `zenn-cli` インストール済 (root package.json + node_modules)
- ✅ `articles/dialogue-delta-hack2026.md` スケルトン作成済 (`published: false`)
- ⬜ AI Club Zenn アカウント未作成
- ⬜ Zenn ↔ GitHub Integration 未設定

## 必要なオペレーション (ブラウザ作業、ユーザー側)

### Step 1: AI Club Zenn アカウント作成

- 既存パターン (memory: `project_hackathon_2026.md`): AI-club サービスは個人 Gmail backed が intentional
- Zenn は GitHub アカウントログインがスムーズ → **`aiclub-labs` Org の admin としてサインアップ**するか、個人アカウントで作成して後で transfer
- 推奨: <https://zenn.dev/> → 「Sign up with GitHub」 → aiclub-labs Org の管理者 GitHub user で
- 表示名: 「AI Club @ Microsoft Agent Hackathon 2026」 等

### Step 2: GitHub リポジトリ連携

1. Zenn ダッシュボード → <https://zenn.dev/dashboard/deploys>
2. 「リポジトリを連携する」 → `aiclub-labs/zenn-hack2026` を選択
3. Zenn は repo root の `articles/` を自動スキャン
4. **Private repo OK** (Zenn Connect は private 対応)

### Step 3: ブランチ運用

- デフォルト: Zenn は `main` ブランチを watch
- 推奨: `articles/*.md` のみ含む PR を main に merge → Zenn が自動 publish (frontmatter `published: true` の記事のみ)
- 別案: 連携時に「published を変えるブランチ」を別途指定可能 (例: `zenn-publish`)

## ローカル CLI フロー

```bash
# プレビュー (http://localhost:8000)
npx zenn preview

# 新規記事
npx zenn new:article --slug <slug> --title "タイトル" --type tech --emoji 💬

# 新規本 (今回は不使用)
npx zenn new:book --slug <slug>
```

## 投稿時の最終チェック

```yaml
# frontmatter
published: false   # ← 完成まで false、提出前に true へ
publication_name: # ← Publication 設定したら追加
topics: ["azure", "openai", "semantickernel", "fastapi", "msahack2026"]
```

- `msahack2026` topic は Hackathon 応募の必須タグ想定 (公式案内を要確認)
- 公開後の修正は再 push で OK (Zenn が自動同期)

## 提出物との対応

| 提出物 | この記事との関係 |
|---|---|
| 動画 mp4 | 記事の §7 にリンク埋め込み |
| 動く App URL | 記事の §7 にリンク埋め込み |
| Markdown 記事 | **本記事 = 提出物本体** |
| GitHub URL | 記事の §7 にリンク埋め込み |

## TODO before 5/31 night

- [ ] AI Club Zenn アカウント作成 (ユーザー)
- [ ] aiclub-labs/zenn-hack2026 を Zenn dashboard に連携 (ユーザー)
- [ ] 記事本文 §1-§8 を埋める (帰宅後)
- [ ] アーキ図 SVG 作成 → `images/` 配下に置く
- [ ] スクショ (Discord 着弾 4 枚, Chat UI, Admin UI) を `images/` に置く
- [ ] `published: true` に変更 → push → Zenn 自動 publish
