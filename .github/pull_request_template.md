## サマリ

<!-- 1〜3 個の bullet で、何を変えたか・なぜ変えたか -->

## スコープ

- [ ] アプリ / エージェントコード（`app/`）
- [ ] UI（`ui/`）
- [ ] インフラ（`infra/`） — `infra-ci.yml` の what-if が走る
- [ ] CI / workflows
- [ ] ドキュメントのみ

## テスト計画

- [ ] `ruff check .` が通る
- [ ] `mypy app` が通る
- [ ] `pytest -q` が通る
- [ ] （インフラ変更時）CI 実行で what-if を確認
- [ ] 手動スモーク: `/health` が ok を返す

## ハッカソンチェックリスト

- [ ] Microsoft AI + Azure コンピュート要件を逸脱していない（提出物に non-Azure コンピュートや non-Microsoft AI が混ざっていない）
- [ ] シークレットを commit していない（`.env`、キー、接続文字列）
- [ ] コスト影響のあるリソースに触れた場合、予算インパクトを記載

## 承認ゲート（Bevy SME モデル — advisory）

> 背景: free-tier private repo では branch protection が使えないため、社会規範で運用する。merge は **2 人 approval** を確認してから。緊急時のソロ merge は Discord `#hack-chat` に事後報告すること。

- [ ] 2 人以上の reviewer の approval を取得した
- [ ] AI レビュー (`@claude-review`) も実行した（オプション、複雑な変更で推奨）
- [ ] CODEOWNERS の指定範囲なら、該当 owner の approval が含まれている

## Discord 反映

- [ ] 設計に関する重要決定なら、`decisions/YYYY-MM-DD-{slug}.md` に ADR を追加した
- [ ] Discord `#hack-dev-log` で議論した内容なら、その forum thread の URL を上記補足に貼った

## 補足

<!-- レビュアーが知っておくべき事項があれば。Discord forum thread URL もここに -->

