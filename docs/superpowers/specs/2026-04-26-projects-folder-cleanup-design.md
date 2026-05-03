# projects/ フォルダ整理 — 設計書

## 概要

`/Users/obatatsunari/projects/` の構造を整理する。変更は最小限（フォルダリネーム + CLAUDE.md更新）。

## 変更内容

### 1. `shift-scheduler/` → `shift_scheduler/` リネーム

- 他のプロジェクトフォルダはすべて snake_case（`apo_list_maker`, `stock_watchlist`, `yt_downloader`）
- `shift-scheduler/` だけ kebab-case になっているため統一する
- `node_modules/` を含むがフォルダごと `mv` するだけで安全

### 2. CLAUDE.md 更新

- `index.html` の位置について注記を追加
  - 「`index.html` = 上座下座チェッカーのメインファイル。`projects/` リポジトリルートに置くことでVercelが自動デプロイする」
- `shift_scheduler/` のセクションを追加（既存フォーマットに準拠）

### 3. `index.html` は移動しない

- `projects/` フォルダ全体が `amiza-shimoza-checker` GitHub リポジトリのルート
- Vercel は `index.html` がリポジトリルートにあることを前提にデプロイしている
- 移動するとVercel設定変更が必要になるため現状維持

## 影響範囲

| 対象 | 変更 | Vercel影響 | git影響 |
|------|------|-----------|---------|
| `shift-scheduler/` | リネーム | なし | フォルダ名変更のみ |
| CLAUDE.md | テキスト追記 | なし | 通常のコミット |
| `index.html` | 変更なし | なし | なし |

## 変更しないもの

- `shift_scheduler/package.json` の `name` フィールド（`"shift-scheduler"` のまま — npmパッケージ名はフォルダ名と一致不要）
- Vercel設定
- 他プロジェクトのフォルダ名・構造
