# YT Downloader — 設計ドキュメント

**日付:** 2026-04-24  
**ステータス:** 承認済み

## 概要

YouTube動画をURLで指定してMP4でダウンロードする、自分専用のローカルWebアプリ。Flask + yt-dlp 構成。

## 要件

- YouTube URLを貼り付けてMP4動画をダウンロードできる
- 利用可能な画質（1080p / 720p / 480p 等）を一覧表示して選択できる
- ダウンロード進捗をリアルタイムのプログレスバーで表示する
- 保存先フォルダをアプリ内で設定・変更できる（`config.json` に永続化）

## ファイル構成

```
projects/
└── yt_downloader/
    ├── app.py                      # Flaskルート
    ├── downloader.py               # yt-dlp ラッパー・進捗フック
    ├── config.json                 # 保存先フォルダ設定（自動生成）
    ├── requirements.txt
    ├── templates/
    │   └── index.html              # UI（1ページ）
    └── YTダウンローダー起動.command
```

## API エンドポイント

| メソッド | パス | 役割 |
|---|---|---|
| GET | `/` | UI表示 |
| POST | `/fetch_qualities` | URL → 利用可能画質一覧をJSON返却 |
| GET | `/download` | `?url=...&quality=...` → SSEで進捗配信 |
| GET | `/config` | 現在の保存先フォルダを返却 |
| POST | `/config` | 保存先フォルダを更新 |

## UI構成

```
┌─────────────────────────────────────┐
│  🎬 YT Downloader                   │
├─────────────────────────────────────┤
│  保存先: /Users/xxx/Downloads  [変更] │
├─────────────────────────────────────┤
│  URL: [___________________________] │
│                      [画質を取得 →]  │
│                                     │
│  画質: ○ 1080p  ○ 720p  ○ 480p      │
│                      [ダウンロード]  │
│                                     │
│  ████████████░░░░  67%  取得中...    │
│  ✓ 完了: video_title.mp4            │
└─────────────────────────────────────┘
```

- 画質選択肢はyt-dlpが実際に取得できるフォーマットのみ表示
- 完了後にファイル名を表示

## 技術詳細

### 進捗ストリーミング（SSE）

- `downloader.py` でyt-dlpの `progress_hooks` コールバックを設定
- フック内で進捗情報を `queue.Queue` に入れる
- Flaskジェネレーター関数でキューを読み取り `yield "data: {...}\n\n"` でSSE配信
- フロントは `EventSource` API で受信し、プログレスバーとパーセント表示を更新

### 設定永続化

- `config.json`: `{"save_dir": "/path/to/folder"}` を保存
- アプリ起動時に読み込み、未存在なら `~/Downloads` をデフォルト設定

### エラーハンドリング

- 無効URL / 非対応URL → `/fetch_qualities` でエラーJSONを返しUI表示
- ダウンロード失敗 → SSEで `event: error` を送信しUI表示
- ffmpeg未インストール → yt-dlpエラーをキャッチして案内メッセージを表示

## 依存ライブラリ

- `flask`
- `yt-dlp`
- ffmpeg（Homebrew経由でインストール: `brew install ffmpeg`）

## 起動方法

`YTダウンローダー起動.command` をダブルクリック、または:

```bash
cd yt_downloader
python3 app.py
# → http://localhost:5002
```

※ port 5001はapo_list_makerが使用中のため5002を使用
