"""Seed: 10 consultant-style "個人ノウハウ" records for general#general.

Domain pivot (2026-05-29):
    Manufacturing/CS から "業務を回す個人の工夫・方法論" 一般 へ pivot。
    sector/unit は単一テナント ``general#general``。Copilot プロンプト型、
    Excel LAMBDA/LET 疑似スクリプト、Power Query 前処理、Office Scripts、
    Power Automate を中心に 10 件を seed する。

    Google Apps Script は外す (社内環境は M365 ベース想定)。

    voting/ranking 機能 (新規) のデモを前提に、各レコードに upvote/downvote
    の初期値を持たせて「人気順」表示が立ち上がりから映える状態にする。

Usage:
  AOAI_API_KEY=... AISEARCH_ADMIN_KEY=... python scripts/seed_consultant_tacit.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
import uuid

AOAI_ENDPOINT = "https://aoai-hack2026.openai.azure.com"
AOAI_DEPLOY = "text-embedding-3-small"
AOAI_KEY = os.environ["AOAI_API_KEY"]

SEARCH_EP = "https://srch-hack2026-dev-ytzykj.search.windows.net"
SEARCH_KEY = os.environ["AISEARCH_ADMIN_KEY"]
INDEX = "corpus-dev"

PK = "general#general"


# --- 5 schema fields under general#general ----------------------------------
# (これらは別途 schemas API 経由で投入する想定。ここでは record.schema_field_id
# の参照キーとして列挙のみ。)
SF_EXCEL = "sf_excel_formula_technique"
SF_PQ = "sf_power_query_recipe"
SF_OS = "sf_office_scripts_macro"
SF_COPILOT = "sf_copilot_prompt_pattern"
SF_PA = "sf_power_automate_flow"


RECORDS = [
    {
        "schema_field_id": SF_EXCEL,
        "title": "LET で長い数式を「変数 + 結果」に分けて可読化する",
        "content": (
            "クライアント提出用の集計シートで、INDEX/MATCH と XLOOKUP を入れ子にした 5 行超の数式は"
            "後任が触れない。LET 関数で中間値に名前を付けると、上から読める疑似スクリプトになる。\n"
            "例: =LET(\n"
            "  顧客行, MATCH([@顧客ID], 顧客マスタ[ID], 0),\n"
            "  契約額, INDEX(顧客マスタ[契約額], 顧客行),\n"
            "  単価, INDEX(顧客マスタ[単価], 顧客行),\n"
            "  IF(契約額>0, 契約額/単価, \"\"))\n"
            "後任の引き継ぎ工数が体感 1/3。マネージャーレビューも数式バーではなく LET 名で会話できる。"
        ),
        "atomic_claims": [
            "LET で中間値に名前付け = 疑似スクリプト化",
            "ネスト深い INDEX/MATCH の引き継ぎコスト削減",
            "レビュー時に変数名で議論可能",
        ],
        "upvotes": 12,
        "downvotes": 1,
    },
    {
        "schema_field_id": SF_EXCEL,
        "title": "LAMBDA で「クライアント別ロジック」を 1 関数化して使い回す",
        "content": (
            "提案フェーズで複数案件分の見積を平行で作るとき、案件ごとに似て非なる集計ロジックが量産される。"
            "LAMBDA で =見積算出(契約額, 期間, 割引率) のような自作関数を定義しておくと、シート間で重複しない。\n"
            "ブックの「名前の管理」に LAMBDA を登録 → 同ブック内ならどのセルからも呼べる。\n"
            "Excel 365 のみ。クライアント送付前に \"値貼り付け\" することで先方環境でも開ける。"
        ),
        "atomic_claims": [
            "LAMBDA で自作関数化",
            "名前の管理に登録するとブック内共有",
            "送付前に値貼り付けで先方環境互換",
        ],
        "upvotes": 8,
        "downvotes": 0,
    },
    {
        "schema_field_id": SF_PQ,
        "title": "Power Query で「日付テキスト揺れ」を一気に正規化する",
        "content": (
            "クライアントから来る一覧で「2025/4/1」「令和7年4月1日」「Apr 1, 2025」が混在するケース。"
            "Power Query で次の順に投げると 90% は片付く:\n"
            "1. Text.Replace で和暦区切りを '/' に揃える\n"
            "2. Date.FromText で第二引数に Culture を ja-JP / en-US 両方試行\n"
            "3. try ... otherwise null で失敗行だけ別 column に逃がす\n"
            "失敗行は最後に目視で潰す方が、全行を VBA でループするより速い。"
        ),
        "atomic_claims": [
            "和暦・西暦・英語混在を 3 ステップで吸収",
            "try-otherwise で失敗行を分離",
            "VBA ループより圧倒的に速い",
        ],
        "upvotes": 15,
        "downvotes": 2,
    },
    {
        "schema_field_id": SF_PQ,
        "title": "縦持ち → 横持ち pivot は \"集約値が 1 つに決まるか\" だけ確認",
        "content": (
            "Power Query の「列のピボット」は集約関数を選ばないと無音で平均値になる罠がある。"
            "業務でやらかすケース TOP3:\n"
            "- 数量列を pivot して \"平均\" が返り、クライアント報告書で数値が半分になる\n"
            "- 同一キーに 2 行ある状態で pivot → Error 列が混入\n"
            "- カウントしたいのに合計を選び、想定の倍\n"
            "対策: 直前ステップで Group By + 集約関数を明示してから pivot。これだけで事故率激減。"
        ),
        "atomic_claims": [
            "PQ pivot のデフォルト集約は平均 (罠)",
            "事前 Group By で集約を明示",
            "事故率激減",
        ],
        "upvotes": 9,
        "downvotes": 0,
    },
    {
        "schema_field_id": SF_OS,
        "title": "Office Scripts で「クライアント別フォーマット差」を 1 関数で吸収",
        "content": (
            "提出フォーマットがクライアント別に微妙に違うとき (列順、ヘッダ名、シート名)、"
            "Office Scripts で main(workbook) の冒頭に「正規化テーブル」を持って switch する。\n"
            "VBA との違いは Power Automate から呼べること。\n"
            "1. デスクトップで Excel → 自動化 → 新しいスクリプト で記録/編集\n"
            "2. パラメータを引数化 (クライアントID 受け取る)\n"
            "3. Power Automate のフローから「スクリプトを実行」アクションでチェーン化\n"
            "毎月の定形整形が完全に消える。"
        ),
        "atomic_claims": [
            "クライアント別揺れを 1 スクリプトで吸収",
            "Power Automate から呼べる (= VBA より有利)",
            "毎月の手作業が消える",
        ],
        "upvotes": 14,
        "downvotes": 1,
    },
    {
        "schema_field_id": SF_OS,
        "title": "テーブル → JSON 変換は Office Scripts の 1 行で十分",
        "content": (
            "Excel の表を Power Automate に渡すとき、values を 2D 配列のまま投げると後段の Parse JSON が"
            "毎回壊れる。Office Scripts で次のように 1 段加工すると安定する:\n"
            "const t = workbook.getTable('対象テーブル');\n"
            "const rows = t.getRangeBetweenHeaderAndTotal().getValues();\n"
            "const headers = t.getHeaderRowRange().getValues()[0];\n"
            "return rows.map(r => Object.fromEntries(r.map((v,i) => [headers[i], v])));\n"
            "JSON の shape が確定するので、Power Automate の各 step で動的コンテンツが選べるようになる。"
        ),
        "atomic_claims": [
            "2D 配列のままだと Parse JSON が壊れる",
            "Object.fromEntries で shape を確定",
            "Power Automate の動的コンテンツが安定",
        ],
        "upvotes": 7,
        "downvotes": 0,
    },
    {
        "schema_field_id": SF_COPILOT,
        "title": "Copilot に議事録を作らせるとき「役割 / 結論 / Next Action」テンプレを必ず渡す",
        "content": (
            "M365 Copilot に「議事録作って」と投げると要約風になるが、コンサルの提出物としては弱い。"
            "プロンプトで以下を強制する:\n"
            "1. 出力フォーマット: '## 議題 / ## 結論 / ## Next Action (担当 + 期日)'\n"
            "2. 発言者の役割明記: 'クライアント PM' / '当方 SM' 等\n"
            "3. 推測禁止: '発言にない結論は書かない'\n"
            "4. 言及されなかった当初アジェンダは 'カバーされず' と明示\n"
            "これで提出可レベルのドラフトに化ける。レビュー工数が体感 1/2。"
        ),
        "atomic_claims": [
            "固定フォーマット指定が必須",
            "発言者の役割明記",
            "推測禁止条項を入れる",
            "未カバー議題を明示させる",
        ],
        "upvotes": 22,
        "downvotes": 1,
    },
    {
        "schema_field_id": SF_COPILOT,
        "title": "Copilot で提案スライドを 1pager に圧縮するときの定型プロンプト",
        "content": (
            "20 枚超の提案スライドをクライアント先で口頭サマリするとき、A4 1 枚に落とす。"
            "プロンプト例:\n"
            "'添付の .pptx を A4 1 枚に圧縮。出力構成: \\n"
            "1. クライアント課題 (3 行)\\n"
            "2. 提案コア (3 行)\\n"
            "3. 期待効果 (定量 1 + 定性 1)\\n"
            "4. 次アクション (3 件、担当・期日付き)\\n"
            "原文にない要素は補わない。スライド N 枚目を根拠引用すること。'\n"
            "根拠引用を強制するとハルシネが激減する。"
        ),
        "atomic_claims": [
            "1pager 構成を 4 ブロックに固定",
            "根拠スライド番号引用を強制",
            "ハルシネ激減",
        ],
        "upvotes": 18,
        "downvotes": 2,
    },
    {
        "schema_field_id": SF_PA,
        "title": "Forms 回答 → Teams 通知の標準フロー (日程調整の即時可視化)",
        "content": (
            "クライアント定例の日程候補を Forms で集めるとき、回答するたびに Teams チャネルへ通知すると"
            "リアルタイムで埋まり方が見えて意思決定が早い。\n"
            "Power Automate テンプレ:\n"
            "1. トリガー: 'Microsoft Forms - 新しい応答が送信されるとき'\n"
            "2. アクション: '応答の詳細を取得'\n"
            "3. アクション: 'Teams にメッセージを投稿' (チャネル固定)\n"
            "本文は Adaptive Card にして「回答者 / 各候補日 ◯×」を 1 行表示。\n"
            "意思決定者が定例で逐次確認 → 締切前に確定できる。"
        ),
        "atomic_claims": [
            "Forms 回答即時を Teams に流す",
            "Adaptive Card で一覧化",
            "日程確定の前倒し",
        ],
        "upvotes": 11,
        "downvotes": 0,
    },
    {
        "schema_field_id": SF_PA,
        "title": "「依頼メール受信 → Excel ログ追加」で SLA トラッキング",
        "content": (
            "クライアントから来る依頼を SLA 管理したいが、専用ツール導入は重い。Power Automate で:\n"
            "1. 'Outlook - 新しいメールが届いたとき' + 件名フィルタ '[依頼]'\n"
            "2. 'Excel - 行を追加' で受信日時/件名/本文/送信者を 1 行追加\n"
            "3. ステータス列はデフォルト '未着手'\n"
            "Excel 側で受信日時 + SLA 営業日数の関数列を持たせると、Power BI なしで「残時間」が見える。"
            "クライアント別 SLA の見える化が即日立ち上がる。"
        ),
        "atomic_claims": [
            "件名フィルタで対象を絞る",
            "Excel 関数で残 SLA を計算",
            "BI ツール不要で即日運用",
        ],
        "upvotes": 13,
        "downvotes": 1,
    },
]


def embed(text: str) -> list[float]:
    req = urllib.request.Request(
        f"{AOAI_ENDPOINT}/openai/deployments/{AOAI_DEPLOY}/embeddings?api-version=2024-08-01-preview",
        data=json.dumps({"input": text}).encode("utf-8"),
        headers={"api-key": AOAI_KEY, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["data"][0]["embedding"]


def upload_batch(docs: list[dict]) -> None:
    payload = {"value": [{"@search.action": "mergeOrUpload", **d} for d in docs]}
    req = urllib.request.Request(
        f"{SEARCH_EP}/indexes/{INDEX}/docs/index?api-version=2024-07-01",
        data=json.dumps(payload).encode("utf-8"),
        headers={"api-key": SEARCH_KEY, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        print(r.status, r.read().decode("utf-8")[:500])


def main() -> int:
    docs: list[dict] = []
    for i, rec in enumerate(RECORDS, start=1):
        text = rec["title"] + "\n" + rec["content"]
        vec = embed(text)
        docs.append(
            {
                "id": f"seed-consultant-{i:02d}-{uuid.uuid4().hex[:6]}",
                "sector": "general",
                "unit": "general",
                "pk": PK,
                "schema_field_id": rec["schema_field_id"],
                "content": text,
                "atomic_claims": rec["atomic_claims"],
                "weight_final": 0.85,
                "shareability": "public",
                "is_active": True,
                "superseded_by": "",
                "created_at": "2026-05-29T03:00:00Z",
                "vector": vec,
                # voting-ready (vote API will overwrite via merge_or_upload):
                "upvotes": rec["upvotes"],
                "downvotes": rec["downvotes"],
                "score": rec["upvotes"] - rec["downvotes"],
                "record_referenced_count": 0,
            }
        )
        print(f"  embedded #{i}: {rec['title'][:40]}")
    upload_batch(docs)
    print(f"\nseeded {len(docs)} records under {PK}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
