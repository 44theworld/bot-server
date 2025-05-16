# Bot Server

このプロジェクトは、LINEおよびDiscordプラットフォーム向けのボットサーバーです。FastAPIを使用して構築されており、Google Cloud Firestoreや外部API（ChatGPT、Google Slides APIなど）と連携しています。

## プロジェクト構成

```
.
├── app/
│   ├── main.py                # FastAPIエントリーポイント
│   ├── api/v1/                # APIエンドポイント
│   │   ├── webhook.py         # Webhookエンドポイント
│   │   ├── vocab_test.py      # 語彙テストAPI
│   │   ├── movie_redirect.py  # 動画リダイレクトAPI
│   ├── core/                  # コア設定とユーティリティ
│   │   ├── config.py          # 環境変数と設定
│   │   ├── firebase.py        # Firestore初期化
│   │   ├── router.py          # ルーティング設定
│   ├── services/              # サービスロジック
│   │   ├── dispatcher.py      # プラットフォームごとのメッセージ振り分け
│   │   ├── platforms/         # プラットフォーム別ロジック
│   │       ├── line/          # LINE関連
│   │       ├── discord/       # Discord関連
│   │   ├── clients/           # 外部APIクライアント
│   ├── static/                # 静的ファイル
│       ├── liff/              # LINE LIFFアプリ
├── Dockerfile                 # Docker設定
├── docker-compose.yml         # Docker Compose設定
├── requirements.txt           # Python依存パッケージ
└── .env                       # 環境変数ファイル（Git管理外）
```

## 主な機能

### LINEボット
- **語彙テスト**: LINE LIFFアプリを使用して語彙レベルを診断。
- **クイズ機能**: 学習した単語をクイズ形式で出題。
- **動画送信**: 学習レベルに応じたYouTube動画を送信。
- **進捗表示**: 学習進捗を表示。

### Discordボット
- **スライド生成**: ChatGPTを使用してメモからGoogleスライドを生成。

## 環境変数

`.env`ファイルで以下の環境変数を設定してください：

- `OPENROUTER_API_KEY`: ChatGPT APIキー
- `SLIDE_CREDENTIALS`: Google Slides APIの認証情報（JSON文字列）
- `FIREBASE_ACCOUNT_FILE`: Firebase認証キーのファイルパス
- `LEVEL_CHECK_LIFF_ID`: LINE LIFFアプリID
- `FASTAPI_URL`: FastAPIのベースURL
- `DISCORD_PUBLIC_KEY`: Discordの公開鍵

## セットアップ

### 1. 必要な依存パッケージをインストール
```bash
pip install -r requirements.txt
```

### 2. Dockerを使用して起動
```bash
docker-compose up --build
```

### 3. ローカルで起動
以下のコマンドでFastAPIサーバーを起動します：
```bash
uvicorn app.main:app --reload
```

## APIエンドポイント

### Webhook
- **URL**: `/api/v1/webhook/{platform}`
- **説明**: LINEまたはDiscordからのリクエストを処理。

### 語彙テスト
- **URL**: `/api/v1/vocab-test/submit`
- **説明**: 語彙テストの結果を送信。
- **URL**: `/api/v1/vocab-test/user-status`
- **説明**: ユーザーの語彙レベルを取得。

### 動画リダイレクト
- **URL**: `/api/v1/redirect/movie`
- **説明**: 動画のURLにリダイレクト。

## 使用技術

- **バックエンド**: FastAPI
- **データベース**: Google Cloud Firestore
- **外部API**:
  - ChatGPT (OpenAI)
  - Google Slides API
- **その他**:
  - LINE Messaging API
  - Discord Interactions API

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
