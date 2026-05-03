# caffeine tracker: JA/EN 言語切り替え (i18n)

## Goal
ページ全体のテキストを日本語・英語でトグルできるようにする。飲み物名・カテゴリを含む全UIテキストが対象。

## Non-goals
- ローカルストレージへの言語設定保存（リロードでJAリセット）
- 3言語以上の対応
- URLベースの言語切り替え（`/en`, `/ja` など）

## Current state
- `caffeine_tracker/index.html` — 単一ファイル（Vanilla JS + SVG）
- UIテキストはすべてHTML直書き（日本語固定）
- ABOUTカードのみ個別EN/JAトグルあり（`aboutLang` 変数 + `aboutLangBtn`）
- DRINKS配列はJAラベル固定

## Design

### UI変更
- ヘッダー（`<header>`）右側に `<button id="langBtn">EN</button>` を追加
- ABOUTカードの個別EN/JAボタン（`#aboutLangBtn`）は削除し、グローバルトグルに統合
- ヘッダーを `display:flex; justify-content:space-between; align-items:center` に変更

### JS アーキテクチャ
```
TEXTS = { ja: { ... }, en: { ... } }   // 全固定テキストを一元管理
DRINKS_I18N = { ja: [...], en: [...] } // 飲み物データも言語別に定義
let currentLang = 'ja'

function toggleLang() {
  currentLang = currentLang === 'ja' ? 'en' : 'ja'
  applyLang(currentLang)
}

function applyLang(lang) {
  // TEXTS[lang] の各エントリを対応IDのDOM要素に反映
  // DRINKSをDRINKS_I18N[lang]に差し替えてselectを再構築
  // ログリストを再描画（飲み物ラベルが切り替わるため）
}
```

### 翻訳対象テキスト

| 要素 | JA | EN |
|---|---|---|
| `#langBtn` | EN | JA |
| セクションラベル "DRINK LOG" | DRINK LOG | DRINK LOG |
| `#addBtn` | + 追加 | + Add |
| ログ空表示 | まだ記録がありません | No entries yet |
| セクションラベル "CAFFEINE LEVEL (mg)" | CAFFEINE LEVEL (mg) | CAFFEINE LEVEL (mg) |
| `#badgeCurrent` label | 現在 | Now |
| `#badgeMidnight` label | 深夜0:00時点 | At midnight |
| `#badge50mg` label | 50mgになる時刻 | Drops to 50mg |
| セクションラベル "ABOUT" | ABOUT | ABOUT |
| `#aboutText` | 既存JA文 | 既存EN文 |

### 飲み物名・カテゴリ翻訳

| カテゴリ JA | カテゴリ EN |
|---|---|
| コーヒー | Coffee |
| お茶 | Tea |
| エナジードリンク | Energy Drink |
| その他 | Other |

飲み物ラベル（例）:

| JA | EN |
|---|---|
| ドリップコーヒー（240ml） | Drip Coffee (240ml) |
| エスプレッソ（1ショット） | Espresso (1 shot) |
| カフェラテ / カプチーノ（240ml） | Café Latte / Cappuccino (240ml) |
| インスタントコーヒー（240ml） | Instant Coffee (240ml) |
| コンビニコーヒー・L（270ml） | Convenience Store Coffee L (270ml) |
| 緑茶（240ml） | Green Tea (240ml) |
| 抹茶ラテ（240ml） | Matcha Latte (240ml) |
| 紅茶（240ml） | Black Tea (240ml) |
| ほうじ茶（240ml） | Hojicha (240ml) |
| ウーロン茶（240ml） | Oolong Tea (240ml) |
| Red Bull（250ml） | Red Bull (250ml) |
| モンスターエナジー（355ml） | Monster Energy (355ml) |
| モンスターエナジー（500ml） | Monster Energy (500ml) |
| コーラ（350ml） | Cola (350ml) |
| 栄養ドリンク（100ml） | Energy Supplement (100ml) |

### ログリスト再描画の注意
言語切り替え時、すでに追加済みのログアイテムのラベルも切り替わる必要がある。  
`entries` 配列には `drink` ID（例: `'drip'`）を保持しているため、`renderLog()` 内で `DRINKS`（現在の言語のリスト）からラベルを引き直せばよい。

### ABOUTカード整理
- `aboutLang` 変数・`toggleAboutLang()` 関数・`ABOUT_TEXT` オブジェクトをすべて削除
- `#aboutLangBtn` 要素を削除
- `#aboutText` の内容は `TEXTS[lang].aboutText` で管理

## Acceptance criteria
- ヘッダーのEN/JAボタンを押すと全UIテキストが切り替わる
- 飲み物名・カテゴリも切り替わる
- 切り替え後にドリンクを追加するとENラベルで記録される
- すでに追加済みのログアイテムのラベルも切り替わる
- ABOUTカードの個別ボタンが消えてグローバルトグルで動く
