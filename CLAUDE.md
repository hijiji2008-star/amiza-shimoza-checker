# 上座下座チェッカー

## プロジェクト概要
出入り口と座席を配置するだけで上座・下座を自動判定するWebツール。
競合となるインタラクティブなチェッカーはなく、SEOでニッチを狙える。

## ファイル構成
- `index.html` — メインファイル（全コードが1ファイルに収まっている）
- `index_redesign.html` — リデザイン試作（和モダン×ブルータリスト、本番未使用）

## 公開情報
- **URL**: https://amiza-shimoza-checker.vercel.app
- **GitHub**: https://github.com/hijiji2008-star/amiza-shimoza-checker
- **ホスティング**: Vercel（GitHubにpushすると自動デプロイ）
- **現在のバージョン**: v1.2.0

## デプロイ方法
```bash
git add index.html
git commit -m "変更内容"
git push
```
pushするだけでVercelが自動で公開してくれる。

## 実装済み機能
- 出入り口を壁に配置（壁クリックで自動判定、モードボタンなし）
- 座席を部屋内に配置（部屋内クリックで自動判定）
- 上座・下座の自動判定・色分け表示
- 座席ランキング表示（サイドバー）
- 出入り口・座席のドラッグ移動
- ダブルクリック／ダブルタップで削除（座席・出入り口）
- 座席未配置時の警告表示（オレンジ強調）
- EN/JA 言語切り替えボタン（全テキスト対応）
- Xシェアボタン・画像保存ボタン（キャンバス下）
- スマホ対応（タッチ操作・ダブルタップ削除・レスポンシブ）
- 「↩ 戻る」ボタン（Undo、Ctrl/Cmd+Zでも動作）
- コンテキストに応じたヒントテキスト（状態連動）

## UI構成
- ヘッダー（タイトル＋EN/JAボタン）
- ツールバー（↩ 戻る・全リセット）→ ヒントボックス → キャンバス → シェア/保存ボタン
- サイドバー（座席ランキング）※凡例・マナーのルールは削除済み

## 操作仕様
- **壁をクリック** → 出入り口を配置（モード切り替え不要）
- **部屋の中をクリック** → 座席を追加
- **ドラッグ** → 座席・出入り口を移動
- **ダブルクリック／ダブルタップ** → 削除
- **↩ 戻る / Ctrl+Z** → 1手アンドゥ

## デザイン
- ダークモダン（フラット）
- 背景: `#0d1117`、カード: `#161b22`
- アクセントカラー: インディゴ→スカイブルーグラデーション

## SEO対策済み
- タイトル・descriptionメタタグ
- OGタグ（SNSシェア用）
- Google Search Console登録済み・インデックス登録リクエスト済み

## toggleLang() の注意点
HTMLのUI要素を削除したら、`toggleLang()` 内の対応する `getElementById` の行も必ず同時に削除すること。
残っているとJSエラーになりそれ以降の翻訳が止まる。

現在 toggleLang() が参照している有効なID:
`langBtn`, `t-title`, `t-undo`, `t-reset`, `t-share`, `t-save`

## 残存デッドコードについて
凡例・マナーのルールUI削除後、以下のコードが残存している（削除してよい）:
- CSS: `.legend-row`, `.legend-dot`, `.rule-text`
- JS翻訳キー: `legend`, `rules`, `ruleText`（JA/EN両オブジェクトに存在）

## 今後やりたいこと
- タクシー・エレベーター・和室などのテンプレート追加
- アクセスが月1,000超えたらGoogle AdSense申請
- 独自ドメイン取得（収益化が見えてきたら）

---

# アポリストメーカー（apo_list_maker/）

派遣会社営業用アポデンリスト自動生成ツール。Indeed Japanをスクレイピングして求人掲載中の企業リストを生成。

## ファイル構成
- `app.py` — Flaskルート（port 5001）
- `scraper.py` — Indeed検索・HTMLパース・フィルタリング・電話番号取得
- `templates/index.html` — フォーム画面 + 結果テーブル
- `tests/test_scraper.py` — スクレイピングロジックの単体テスト

## 起動方法
```bash
cd apo_list_maker
python3 app.py   # → http://localhost:5001
```
※ port 5000はmacOS AirPlay Receiverが使用中のため5001を使う

## 開発上の注意
- Playwright インストール: `python3 -m playwright install chromium`（`playwright` コマンドはPATHにない）
- Indeed: `requests`は403。Playwrightで `wait_until="domcontentloaded"` + 3秒待機で動作
- 電話番号取得: Yahoo Japan検索が動作。Google・iタウンページはPlaywrightでもブロックされる

---

# 1日スケジュールプランナー（schedule-planner.html）

AM/PM ドーナツグラフで1日の予定を可視化するWebツール。単一HTMLファイル。

## 実装済み機能
- AM/PMの2つのドーナツ円グラフ（SVG、Vanilla JS）
- グラフリングをクリック/タップして開始・終了時刻をセット（2タップ式、30分スナップ）
- ホバーインジケーター（白ドット→ゴースト弧→STARTドット）
- サイドバーフォームに時刻を自動入力、活動名にフォーカス移動
- ESC・リング外クリックで tapState リセット
- ローカルストレージ永続化、日またぎ活動対応

## 状態管理
- `tapStateAM / tapStatePM`: `null | { startMin: number }` — 1回目タップでSTART確定、2回目でEND確定
- `hoverMinAM / hoverMinPM`: ホバー中の30分スナップ位置

## SVG タッチイベントの注意点
- `getSVGCoords(svg, event)` は `event.touches[0]` を参照するため **touchend では使えない**（touchend時は touches が空）。touchend では `e.changedTouches[0]` を直接使うこと。
- `xyToMin` のクランプ上限は `periodStart + 690`（+720にすると PM で `"24:00"` が生成され `<input type="time">` が無効値になる）
- ゴースト弧の span 計算: `(endAngle - startAngle + 360) % 360` は startMin=periodStart かつ hoverMin=periodStart+720 のとき 0 になり弧が消える。条件に `&& hoverMin < periodStart + 720` を入れること。

## 開発上の注意
- ブラウザテストに Playwright MCP を使うとスクリーンショットがルートに吐き出される → セッション後に削除すること
- `.playwright-mcp/` `.superpowers/` は `.gitignore` 済み
