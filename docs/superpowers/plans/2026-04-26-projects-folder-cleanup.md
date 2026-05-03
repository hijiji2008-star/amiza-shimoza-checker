# projects/ フォルダ整理 実装プラン

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `projects/` フォルダの構造を整理する（フォルダリネーム + CLAUDE.md更新）

**Architecture:** `shift-scheduler/` を snake_case に統一し、CLAUDE.md に `shift_scheduler` と `index.html` の位置について明記する。コード変更なし。

**Tech Stack:** bash (mv), git

---

### Task 1: shift-scheduler/ を shift_scheduler/ にリネーム

**Files:**
- Rename: `shift-scheduler/` → `shift_scheduler/`

- [ ] **Step 1: フォルダをリネーム**

```bash
mv /Users/obatatsunari/projects/shift-scheduler /Users/obatatsunari/projects/shift_scheduler
```

- [ ] **Step 2: リネーム確認**

```bash
ls /Users/obatatsunari/projects/
```

期待される出力: `shift_scheduler` が存在し、`shift-scheduler` が消えていること

---

### Task 2: .gitignore を更新

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: .gitignore の `shift-scheduler/` エントリを `shift_scheduler/` に変更**

`.gitignore` の以下の3行を:
```
# shift-scheduler
shift-scheduler/node_modules/
shift-scheduler/dist/
shift-scheduler/.vite/
```

以下に変更:
```
# shift_scheduler
shift_scheduler/node_modules/
shift_scheduler/dist/
shift_scheduler/.vite/
```

- [ ] **Step 2: 確認**

```bash
git -C /Users/obatatsunari/projects status
```

期待される出力: `shift-scheduler/` の削除と `shift_scheduler/` の追加が表示される（node_modules は除外されている）

---

### Task 3: CLAUDE.md を更新

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: 上座下座チェッカーセクションに `index.html` の位置についての注記を追加**

`## ファイル構成` セクションを以下に変更:

```markdown
## ファイル構成
- `index.html` — メインファイル（全コードが1ファイルに収まっている）。`projects/` リポジトリルートに置くことでVercelが自動デプロイする
- `index_redesign.html` — リデザイン試作（和モダン×ブルータリスト、本番未使用）
```

- [ ] **Step 2: CLAUDE.md 末尾に `shift_scheduler` セクションを追加**

`yt_downloader` セクションの末尾の `---` の後に以下を追加:

```markdown

---

# シフトスケジューラー（shift_scheduler/）

従業員のシフトを管理するWebアプリ。React + Vite + Tailwind CSS。

## ファイル構成
- `src/App.jsx` — エントリポイント
- `src/components/ShiftScheduler.jsx` — メインコンポーネント
- `index.html` — Viteエントリ

## 起動方法
```bash
cd shift_scheduler
npm run dev   # → http://localhost:5173
```

## ビルド
```bash
npm run build   # dist/ に出力
```

## 開発上の注意
- React 18 + Vite 5 + Tailwind CSS 3
- `package.json` の `name` フィールドは `"shift-scheduler"`（kebab）のまま — npmパッケージ名はフォルダ名と一致不要
```

- [ ] **Step 3: 確認**

```bash
grep -n "shift_scheduler\|index.html.*Vercel" /Users/obatatsunari/projects/CLAUDE.md
```

期待される出力: `shift_scheduler` セクションと `index.html` のVercel注記が含まれていること

---

### Task 4: コミット

- [ ] **Step 1: 変更をステージ**

```bash
git -C /Users/obatatsunari/projects add .gitignore CLAUDE.md
git -C /Users/obatatsunari/projects add shift_scheduler
```

- [ ] **Step 2: コミット**

```bash
git -C /Users/obatatsunari/projects commit -m "$(cat <<'EOF'
refactor: shift-schedulerをsnake_caseにリネーム + CLAUDE.md更新

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: 確認**

```bash
git -C /Users/obatatsunari/projects log --oneline -3
```
