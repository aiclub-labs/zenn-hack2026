# D2: 製造ライン 品質管理 / 技能継承 — ¥ ビジネスインパクト試算

> 用途: Microsoft Agent Hackathon Japan 2026 デモピッチの根拠資料
> 対象: 日本国内 中堅製造業 (自動車部品 Tier 2 / 電子部品 / 食品加工 のいずれか) の 1 工場 1 ライン
> 作成日: 2026-05-27 / 検証レベル: 出典付き一次仮説 (本気の提案前に「最後の追加検証」セクション要対応)

## 1. 典型顧客像

| 項目 | 想定値 | 補足 |
|------|--------|------|
| 業種例 | 自動車部品 Tier 2 (プレス・樹脂成形・電装) / 電子部品 (コネクタ・基板実装) / 食品加工 (惣菜・冷食) | 「ベテランの勘」依存度が高く、官能検査が残る領域 |
| 企業規模 | 従業員 100-2,000 人、年商 **10-1,000 億円** (政府新定義「中堅企業」帯) | 中堅企業 = 資本金 3 億円以上 + 常用 301-2,000 人 [経産省](https://www.meti.go.jp/policy/economy/keiei_innovation/keieiryoku/index.html) / 中堅売上目安 10-1,000 億 [起業ログ](https://kigyolog.com/article.php?id=1597) |
| 工場規模 | 1 拠点 / ライン 3-8 本 / 1 ライン年商寄与 **20-50 億円** | 自動車部品 Tier 2 で年商 100 億クラスは中堅上位帯、ライン 5 本前提で 1 本 20 億は妥当域 |
| 現場構成 (1 ライン) | 班長 1 + 熟練工 2-3 + 一般 5-8 + 新人 2-3 = 約 10-15 名 | ものづくり白書 2025 (中小製造業 OFF-JT 実施率の差) [METI](https://www.meti.go.jp/report/whitepaper/mono/2025/pdf/gaiyo.pdf) |
| PC 環境 | 現場 PC は班長卓 1 台 + 検査端末 / 作業者は基本 PC なし。スマホ持込制限ありの工場多数 | C5 課題の根拠 |

> ピッチ用代表値: **「ライン 1 本 = 年商 30 億円」**。後段の ¥ 計算はこれを基準にする。元ピッチの「¥100 億ライン」は中堅単一ラインの実態より過大 (Tier 1 規模)。

## 2. 主要 KPI ベンチマーク

| KPI | 値 (日本) | 出典 |
|-----|----------|------|
| **不良率 目安 (一般製造)** | 3σ 管理 = **0.27%** (1,000 個に 2.7 個)。多くの中堅工場の実運用域 | [i-Reporter 解説](https://i-reporter.jp/column/14809/)、[PROTRUDE](https://protrude.com/report/defectiverate/) |
| **不良率 目安 (自動車部品・医療・航空)** | 6σ = **0.00034%** (100 万個に 3.4 個) を目標、PPM 管理が標準。実運用は **数十〜数百 PPM** 帯 | [i-Reporter](https://i-reporter.jp/column/14809/)、[SmartMat](https://www.smartmat.io/column/production_management/8208) |
| **不良率 目安 (一般民生品・樹脂玩具等)** | 3σ 〜 数% (1-3%) | [i-Reporter](https://i-reporter.jp/column/14809/) |
| **熟練工 養成期間** | 一人前まで **10 年以上** を要する技能あり。短期間の継承は不可能 | [JSTAGE 熟練技能の現状](https://www.jstage.jst.go.jp/article/sicejl1962/37/7/37_7_490/_pdf)、[厚労省 ものづくりマイスター制度](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/jinzaikaihatsu/monozukuri_master/index.html) |
| **新人 → 戦力化** | 製品・工程により **1-3 年** が現実的中央値 (短縮事例: 2 年 → 1 年) | [Learnify 2025 問題と技術伝承](https://learnify.jp/blog/archives/1401) |
| **人材育成 時間不足** | 育成課題ありの事業所のうち **49.4%** が「人材育成を行う時間がない」 | [厚労省 ものづくり白書 2025 概要](https://www.mhlw.go.jp/content/001496473.pdf) |
| **製造業 就業者数** | 2024 年 **1,046 万人** (20 年で 157 万人減)。65 歳以上比率はこの 20 年で倍増 | [METI ものづくり白書 2025 第1部第2章](https://www.meti.go.jp/report/whitepaper/mono/2025/pdf/honbun_1_2_1.pdf) |
| **指導役の退職** | 製造業企業の約 **60%** が「指導役となるベテラン技能者の退職」を人材不足要因に挙げる | [METI 製造業を巡る動向](https://www.meti.go.jp/shingikai/sankoshin/seizo_sangyo/pdf/009_02_00.pdf) (ものづくり白書 2025 引用) |
| **2030 年問題 (製造業 高齢就業者)** | 製造業就業者の若年層 (34 歳以下) は大幅減、65 歳以上比率倍増 → 2030 年に向け熟練層大量退職の山が継続 | [METI ものづくり白書 2025](https://www.meti.go.jp/report/whitepaper/mono/2025/pdf/honbun_1_2_1.pdf) |
| **ベテラン vs 新人 判断ギャップ** | 定量論文なし (要追検)。実務記事ベースでは「音・振動・色味」での異常検知再現率に大きな差。AI 異音検知で「経験 20 年の耳」を数値化できると報告 | [エムニ 異音検知 AI](https://media.emuniinc.jp/2024/12/31/abnormal-sound-detection-ai-2/)、[現場コンパス](https://genbacompass.com/blog/genbacompass/knowhow_manufacturing-quality-technology-succession) |

## 3. ¥ 効果計算式 (transparent)

**前提**: ライン 1 本年商 **30 億円**、変動費率 70%、現状不良率 **1.0%** (3σ より少しゆるめの中堅実態想定。自動車部品 Tier 1 ではなく Tier 2 / 民生品帯)。直接材ロス + 手戻り + クレーム対応 + ラインストップで「不良 1pt = 売上高比 0.6-1.0% 相当」とする業界経験則を採用。

¥ 換算経路は 3 つ:
- (A) **歩留改善** = 不良 -X pt × 売上高 30 億 × 換算係数
- (B) **教育期間短縮** = 新人立上げ短縮分の生産性回復 + 熟練工の指導工数解放
- (C) **設備停止削減** = 設備別根本原因判断の精度向上で MTTR / 原因誤判定の手戻り削減 (今回は控えめに保留)

| シナリオ | 不良率改善 | 教育期間 | 経路別内訳 | 効果/年 |
|---------|-----------|---------|-----------|--------|
| **保守 (Conservative)** | 1.0% → **0.7%** (-0.3pt) | 24 ヶ月 → 18 ヶ月 (-25%) | (A) 30 億 × 0.3% × 換算 0.7 = **630 万円**<br>(B) 新人 3 名 × 6 ヶ月短縮 × 立上期生産性差 30 万/月 = **540 万円**<br>(C) 熟練工 1 名の指導工数 -20% × 人件費 800 万 = **160 万円** | **約 0.13 億円/年** |
| **中位 (Mid)** | 1.0% → **0.5%** (-0.5pt) | 24 ヶ月 → 12 ヶ月 (-50%) | (A) 30 億 × 0.5% × 換算 0.8 = **1,200 万円**<br>(B) 新人 3 名 × 12 ヶ月 × 30 万 = **1,080 万円**<br>(C) 熟練工 2 名指導工数 -30% = **480 万円** | **約 0.28 億円/年** |
| **楽観 (Optimistic)** | 1.0% → **0.3%** (-0.7pt) | 24 ヶ月 → 8 ヶ月 (-67%) | (A) 30 億 × 0.7% × 換算 1.0 = **2,100 万円**<br>(B) 新人 5 名 × 16 ヶ月 × 30 万 = **2,400 万円**<br>(C) 熟練工 3 名指導工数 -40% + クレーム対応 -30% = **1,000 万円** | **約 0.55 億円/年** |

**式の前提 (明示)**:
- (A) 換算係数 0.7-1.0 = 直接材 + 手戻り工数 + 廃棄処分 + 出荷後不良の引当を粗合算。業界によって差大 (食品は廃棄比重大、電子部品は手戻り比重大)
- (B) 「立上期生産性差 30 万円/月」= 新人月給 25 万 + 教官工数 15 万 のうち、戦力化前は 50% 生産性 → 機会損失 20 万 + 教官時間 10 万 ≈ 30 万/月
- (C) 熟練工人件費 800 万/年、指導工数は通常 20-30% を占めるという現場ヒアリング知見 (要裏取り)
- **元ピッチの「¥1.5 億/年」は、ライン年商 30 億前提では再現不可。100 億ライン (Tier 1 規模) なら中位シナリオで届くが、その場合は中堅でなく大手案件**

**結論**: デモピッチは **「ライン年商 30 億 × 1 ライン = 0.13-0.55 億/年、複数ライン展開で工場全体 0.5-2.5 億/年」** のレンジで提示。元ピッチを使うなら「複数ライン × 中位」前提を明示。

## 4. 競合 / 既存ソリューション

| プレイヤー | 強み | 我々との差別化軸 |
|-----------|------|------------------|
| **日立 Lumada 3.0 / Physical AI** ([Biz/Zine](https://bizzine.jp/article/detail/12752)、[Hitachi](https://www.hitachi.co.jp/products/it/lumada/spcon/generative_ai/overview/index.html)) | 大手向け統合プラットフォーム、生成 AI エージェント、フィジカル AI 構想 | 我々は **対話駆動の暗黙知抽出 (5W1H + Delta Detector)** に特化。日立はセンサー / 自動化主導、我々は人間対話の構造化主導 |
| **HACARUS Check** ([HACARUS](https://check.hacarus.com/ja/lp/)) | 少量データ AI 外観検査、検査員 6 → 2 名削減実績 | HACARUS は「検査の自動化」、我々は「検査ノウハウの言語化と継承」。対象タスクが補完関係 |
| **電通総研 (旧 ISID)** ([暗黙知の形式知化](https://mfg.dentsusoken.com/blog/detail/001827.php)) | FA 領域コンサル + 形式知化フレームワーク | コンサル提供型、ツール化されていない。我々は **アプリ化された対話 UI + スキーマ管理 CRUD** で現場運用可能 |
| **DCS 暗黙知 AI 実証** ([DCS](https://www.dcs.co.jp/technology/report/manufacture/index.html))、**慶大 匠和会** ([日経 xTECH](https://xtech.nikkei.com/atcl/nxt/column/18/00001/11591/)) | 業界連合・学術ベースの取り組み | まだ実証段階。我々は **マルチエージェント (Hearout / Delta Detector / Truth Judgment) でリアルタイム対話補助** に踏み込む |

**差別化サマリ**: 既存は (a) 自動検査 / (b) コンサル形式知化 / (c) 学術実証 のいずれか。**「専門家 × 新人の対話を 5W1H スキーマでリアルタイム構造化し、差分検知でツッコミを入れる」エージェント**は競合空白域。

## 5. 暗黙知の典型例 (D2 領域)

| 知識ドメイン | 言語化困難な経験知 | 出典 |
|-------------|------------------|------|
| **異音検知** | 「ベアリングが鳴く前の高周波の予兆」「正常時と異常時のうなり周波数差」を耳で聞き分け | [エムニ 異音検知 AI](https://media.emuniinc.jp/2024/12/31/abnormal-sound-detection-ai-2/)、[トラスト](https://trust-coms.com/trust-note/1932/) |
| **振動・触覚** | 機械の振動の質的変化を手で感知、「いつもと違う」を 1 秒で判別 | [現場コンパス](https://genbacompass.com/blog/genbacompass/knowhow_manufacturing-quality-technology-succession) |
| **色味・外観** | 樹脂成形のショート / バリ / シルバーストリーク / ヒケの微妙な色調差。光源条件込みで判断 | [PROTRUDE 形式知/暗黙知](https://protrude.com/report/km-explicitandracitknowledge/) |
| **設備別根本原因** | 「この音 + この時期 + この材料ロット = 高確率で〇〇の摩耗」という多変数複合判断 | [DCS 実証](https://www.dcs.co.jp/technology/report/manufacture/index.html) |
| **段取り・勘所** | 加工条件 (送り速度・温度) の微調整、季節 / 湿度補正 | [PROTRUDE](https://protrude.com/report/km-explicitandracitknowledge/) |

→ 我々のアプリは **対話を通じて「いつもと違う = 何が、どの基準と、どれくらい違うか」を 5W1H で問い直し、Delta Detector が差分を抽出、Truth Judgment が複数情報源と突合** する。「音が変」を「2,800Hz 付近の高調波が通常比 +8dB、ベアリング Cf 3 番系」まで形式知化するのが狙い。

## 6. C5 (デモ説得力) 補強策 — 現場 PC 制約への解

| 弱点 | 補強策 |
|------|--------|
| 作業者は基本 PC なし、スマホ持込制限 | **タブレット (堅牢型 / 防塵防滴) を班長 + 熟練工に各 1 台**。Microsoft Surface Pro / Panasonic TOUGHBOOK 想定 |
| 手が塞がる / 騒音環境 | **音声入力 (Azure Speech to Text) + 簡易タップ UI**。Wear OS or Bluetooth ピンマイク選択肢 |
| 画面映え弱 (作業中の地味さ) | デモは **「熟練工と新人の対話 → リアルタイム 5W1H 構造化 → Delta 抽出 → 検査基準書ドラフト自動生成」** の 3 分動線で見せる。Before/After (構造化前テキスト → 構造化後スキーマ) のコントラストを大きく |
| 工場長レビュー必須の組織文化 | **承認フロー UI (工場長カード) を画面内に組み込み**、「現場で対話 → 工場長 1 タップで承認 → 標準化文書化」を 1 画面に圧縮 |
| 個人依存 / 評価への抵抗 | デモシナリオで「ベテランの知見が組織財産になる」フレームを明示 (ベテラン側の心理障壁緩和) |

## 7. 出典一覧

1. [経済産業省 / 厚労省 / 文科省『2025 年版 ものづくり白書』概要](https://www.meti.go.jp/report/whitepaper/mono/2025/pdf/gaiyo.pdf)
2. [METI『ものづくり白書 2025』第1部第2章 (就業動向と人材確保・育成)](https://www.meti.go.jp/report/whitepaper/mono/2025/pdf/honbun_1_2_1.pdf)
3. [厚生労働省『2025 年版 ものづくり白書』概要](https://www.mhlw.go.jp/content/001496473.pdf)
4. [METI 産構審 製造産業分科会『製造業を巡る動向と今後の課題』](https://www.meti.go.jp/shingikai/sankoshin/seizo_sangyo/pdf/009_02_00.pdf)
5. [厚生労働省『若年技能者人材育成支援等事業 (ものづくりマイスター制度)』](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/koyou_roudou/jinzaikaihatsu/monozukuri_master/index.html)
6. [JSTAGE『製造現場における熟練技能の現状』 (計測自動制御学会誌)](https://www.jstage.jst.go.jp/article/sicejl1962/37/7/37_7_490/_pdf)
7. [i-Reporter『製造業における不良率とは？計算方法や目安、許容範囲を解説』](https://i-reporter.jp/column/14809/)
8. [SmartMat『不良率 定義・PPM・歩留まり・許容範囲・原因と改善策』](https://www.smartmat.io/column/production_management/8208)
9. [Biz/Zine『日立が挑む「フィジカルAI」の実装』 (Lumada 3.0)](https://bizzine.jp/article/detail/12752)
10. [HACARUS Check 製品サイト (外観検査 AI 導入事例)](https://check.hacarus.com/ja/lp/)
11. [日経 xTECH『製造業の暗黙知を AI で継承へ、慶大・栗原教授らが業界団体を発足』](https://xtech.nikkei.com/atcl/nxt/column/18/00001/11591/)
12. [DCS『製造業・熟練技能者の暗黙知を AI に代替させる実証実験』](https://www.dcs.co.jp/technology/report/manufacture/index.html)
13. [エムニ『異音検知 (異常音検知) AI とは？』](https://media.emuniinc.jp/2024/12/31/abnormal-sound-detection-ai-2/)
14. [Learnify『2025 年問題と技術伝承』 (養成期間短縮事例)](https://learnify.jp/blog/archives/1401)
15. [PROTRUDE『形式知と暗黙知、製造業での成功事例と失敗から学ぶ』](https://protrude.com/report/km-explicitandracitknowledge/)

## 8. この数字を本気で出すなら追加検証すべき点

1. **業種別不良率の中央値の一次データ**: 日本品質管理学会 / JSA / 日科技連の業種別ベンチマーク (一般公開資料に乏しい)。今回は σ 管理の理論値どまり。Tier 2 自動車部品の実運用値 (PPM 帯) を業界団体ヒアリングで取得すべき。
2. **¥ 換算係数 0.7-1.0 の裏取り**: 「不良 1pt = 売上比 X%」の換算は業種で大きく振れる。自動車部品 (リコール影響大) / 食品 (廃棄重) / 電子 (再ワーク重) で別係数が必要。具体的なヒアリング先 1-2 社確保が望ましい。
3. **熟練工指導工数の比率**: 「20-30%」は感覚値。中堅工場 3 社程度の作業日報サンプリングで実測すべき。
4. **ベテラン vs 新人 判断ギャップの定量論文**: 異音検知精度・色味判別精度の人間 vs 経験年数の比較研究を探す (人間工学会・精密工学会・SICE)。今回は実務記事のみ。
5. **デモ顧客の年商 / ライン数の現実プロファイル**: ¥1.5 億達成には複数ライン展開が前提。デモ顧客が「ライン 5 本以上 + 年商 100-300 億」の帯に実在するか、商談ターゲットリスト (帝国データ / 東商工リサーチの中堅製造業セグメント) で件数を確認すべき。
