# BigQuery Remote MCP Server + ADK Agent セットアップガイド

Google Cloud の BigQuery Remote MCP Server を使用して、ADK エージェントから動的に BigQuery を操作する方法を説明します。

## 目次

1. [クイックスタート](#クイックスタート)
2. [プロジェクト構成](#プロジェクト構成)
3. [前提条件](#前提条件)
4. [gcloud CLI セットアップ](#gcloud-cli-セットアップ)
5. [環境構築](#環境構築)
6. [GCP設定](#gcp設定)
7. [MCP Server 有効化](#mcp-server-有効化)
8. [ローカルテスト](#ローカルテスト)
9. [Agent Engineへのデプロイ](#agent-engineへのデプロイ)
10. [デプロイ後のテスト](#デプロイ後のテスト)
11. [エージェントの更新](#エージェントの更新)
12. [Gemini Enterpriseでの設定](#gemini-enterpriseでの設定)
13. [トラブルシューティング](#トラブルシューティング)

---

## クイックスタート

既に環境が整っている場合の最短手順：

```bash
# 1. リポジトリをクローン
git clone https://github.com/YOUR_USERNAME/bq-mcp-agent.git
cd bq-mcp-agent

# 2. .env ファイルを作成
cp .env.example .env
# .env を編集してプロジェクトIDを設定

# 3. セットアップ実行
./setup.sh

# 4. ローカルテスト
source .venv/bin/activate
adk web
# http://localhost:8000 でテスト

# 5. Agent Engine にデプロイ
./deploy.sh

# 6. デプロイしたエージェントをテスト
python test_agent.py
```

---

## プロジェクト構成

```
bq-mcp-agent/
├── .env.example          # 環境変数テンプレート
├── .env                   # 環境変数（git管理外）
├── .gitignore             # Git除外設定
├── SETUP_GUIDE.md         # このドキュメント
├── requirements.txt       # 依存パッケージ
│
├── setup.sh               # 環境セットアップスクリプト
├── deploy.py              # デプロイ用Pythonスクリプト
├── deploy.sh              # デプロイ実行スクリプト
├── test_agent.py          # テストスクリプト
│
└── bq_agent/              # エージェント本体
    ├── __init__.py
    └── agent.py           # エージェント定義
```

### 各ファイルの役割

| ファイル | 説明 |
|---------|------|
| `setup.sh` | 初回セットアップ（API有効化、権限設定、仮想環境作成） |
| `deploy.sh` | Agent Engine へのデプロイ実行 |
| `deploy.py` | デプロイロジック（権限設定、バケット作成、adk deploy実行） |
| `test_agent.py` | デプロイしたエージェントの対話式テスト |
| `bq_agent/agent.py` | エージェントの定義（LLM、ツール、プロンプト） |

---

## 前提条件

- Python 3.11以上
- Google Cloud アカウント
- gcloud CLI **最新版**（MCP機能にはv500以上推奨）
- uv パッケージマネージャー（推奨）

---

## gcloud CLI セットアップ

### gcloud CLI のインストール（未インストールの場合）

#### macOS

```bash
# Homebrew でインストール
brew install google-cloud-sdk

# または公式インストーラー
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

#### Windows

[Google Cloud SDK インストーラー](https://cloud.google.com/sdk/docs/install?hl=ja) をダウンロードして実行

#### Linux

```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### gcloud CLI のバージョン確認とアップデート

```bash
# 現在のバージョンを確認
gcloud version

# 最新版にアップデート（重要！MCP機能には最新版が必要）
gcloud components update

# beta コンポーネントをインストール（MCP有効化に必要）
gcloud components install beta

# アップデート後にバージョン再確認
gcloud version
```

> ⚠️ **重要**: `gcloud beta services mcp` コマンドを使用するには、gcloud CLI の最新版が必要です。エラーが出る場合は必ずアップデートしてください。

### gcloud CLI の認証

```bash
# gcloud CLIにログイン
gcloud auth login

# Application Default Credentials (ADC) を設定
gcloud auth application-default login
```

---

## 環境構築

### 1. uv のインストール（未インストールの場合）

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Homebrew (macOS)
brew install uv
```

### 2. リポジトリをクローン

```bash
git clone https://github.com/YOUR_USERNAME/bq-mcp-agent.git
cd bq-mcp-agent
```

### 3. uv で仮想環境とパッケージをセットアップ

```bash
# Python 3.11 で仮想環境を作成
uv venv --python 3.11

# 仮想環境を有効化
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# パッケージをインストール
uv pip install -r requirements.txt
```

---

## GCP設定

### 1. プロジェクト設定

```bash
# プロジェクトIDを環境変数に設定（自分のプロジェクトIDに変更）
export PROJECT_ID="your-project-id"

# プロジェクトを設定
gcloud config set project $PROJECT_ID

# 設定確認
gcloud config get project
```

### 2. 必要なAPIを有効化

```bash
# BigQuery API
gcloud services enable bigquery.googleapis.com --project=$PROJECT_ID

# Vertex AI API (Agent Engine用)
gcloud services enable aiplatform.googleapis.com --project=$PROJECT_ID

# Cloud Resource Manager API
gcloud services enable cloudresourcemanager.googleapis.com --project=$PROJECT_ID

# API Hub API (MCP用)
gcloud services enable apihub.googleapis.com --project=$PROJECT_ID

# Cloud API Registry API (MCP用)
gcloud services enable cloudapiregistry.googleapis.com --project=$PROJECT_ID
```

### 3. ユーザーに権限を付与

```bash
# 自分のメールアドレスを設定
export USER_EMAIL="your-email@example.com"

# BigQuery 権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$USER_EMAIL" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$USER_EMAIL" \
  --role="roles/bigquery.jobUser"

# MCP Tool User ロールを付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$USER_EMAIL" \
  --role="roles/mcp.toolUser"
```

---

## MCP Server 有効化

### BigQuery Remote MCP Server を有効化

> ⚠️ **注意**: この手順には gcloud CLI の**最新版**と **beta コンポーネント**が必要です。
> エラーが出る場合は [gcloud CLI セットアップ](#gcloud-cli-セットアップ) を参照してください。

```bash
# gcloud beta コンポーネントがインストールされているか確認
gcloud components list | grep beta

# インストールされていない場合
gcloud components install beta

# BigQuery MCP Server を有効化
gcloud beta services mcp enable bigquery.googleapis.com --project=$PROJECT_ID
```

### 有効化の確認

```bash
# MCP Server のステータスを確認
gcloud beta services mcp list --project=$PROJECT_ID
```

成功すると以下のように表示されます：

```
SERVICE                     MCP_STATUS
bigquery.googleapis.com     ENABLED
```

### MCP Server のエンドポイント

有効化後、以下のエンドポイントが使用可能になります：

- **URL**: `https://bigquery.googleapis.com/mcp`
- **Protocol**: Streamable HTTP (MCP over HTTP)

---

## ローカルテスト

### 1. .env ファイルを編集

`.env` ファイルを開き、プロジェクトIDを自分のものに変更：

```
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=1
```

### 2. 環境変数を読み込み

```bash
# .env ファイルの内容を環境変数に設定
export $(grep -v '^#' .env | xargs)

# 確認
echo $GOOGLE_CLOUD_PROJECT
```

### 3. ADK Web UI で起動

```bash
adk web
```

### 4. ブラウザでアクセス

http://localhost:8000 にアクセスし、エージェントをテスト

**テスト用の質問例:**
- 「BQにどんなデータがありますか？」
- 「○○データセットのテーブル一覧を見せて」
- 「○○テーブルのスキーマを教えて」
- 「○○テーブルから10件取得して」

---

## Agent Engineへのデプロイ

Agent Engine にデプロイすることで、本番環境でエージェントを実行できます。

### デプロイ方法

#### 方法1: deploy.sh を使用（推奨）

最も簡単な方法です。以下のコマンドで自動的にデプロイされます：

```bash
./deploy.sh
```

このスクリプトは以下を自動実行します：
- 環境変数の読み込み（.env）
- 仮想環境の有効化
- サービスアカウントへの権限付与
- ステージングバケットの作成（必要な場合）
- Agent Engine へのデプロイ
- デプロイ結果の確認

**オプション:**

```bash
# 表示名を指定
./deploy.sh --display-name "BQ Agent v2"

# 権限設定をスキップ（既に設定済みの場合）
./deploy.sh --skip-permissions

# カスタムステージングバケットを使用
./deploy.sh --staging-bucket gs://my-custom-bucket
```

#### 方法2: deploy.py を直接実行

Python スクリプトを直接実行することもできます：

```bash
source .venv/bin/activate

python deploy.py \
  --project your-project-id \
  --region us-central1 \
  --display-name "BQ Agent"
```

**deploy.py のオプション:**

| オプション | 短縮形 | 説明 | デフォルト |
|-----------|-------|------|----------|
| `--project` | `-p` | GCPプロジェクトID | 環境変数から取得 |
| `--region` | `-r` | デプロイ先リージョン | us-central1 |
| `--display-name` | `-n` | エージェントの表示名 | なし |
| `--staging-bucket` | `-b` | GCSステージングバケット | 自動生成 |
| `--skip-permissions` | | 権限設定をスキップ | False |
| `--agent-dir` | | エージェントディレクトリ | ./bq_agent |

#### 方法3: adk コマンドを直接使用

手動でデプロイする場合：

```bash
# 1. 環境変数設定
export PROJECT_ID="your-project-id"

# 2. プロジェクト番号を取得
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

# 3. サービスアカウントに権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
  --role="roles/mcp.toolUser"

# 4. ステージングバケット作成（初回のみ）
gcloud storage buckets create gs://${PROJECT_ID}-adk-staging \
  --project=$PROJECT_ID \
  --location=us-central1

# 5. デプロイ実行
adk deploy agent_engine \
  --project=$PROJECT_ID \
  --region=us-central1 \
  --staging_bucket=gs://${PROJECT_ID}-adk-staging \
  ./bq_agent
```

### デプロイ結果

デプロイ完了後、**Resource ID** が表示されます：

```
Deployed agent to: projects/YOUR_PROJECT/locations/us-central1/reasoningEngines/RESOURCE_ID
```

この Resource ID は後でテストや Gemini Enterprise 連携に使用します。

### デプロイ確認

```bash
# デプロイされたエージェント一覧を確認
gcloud ai reasoning-engines list \
  --project=$PROJECT_ID \
  --region=us-central1

# 特定のエージェントの詳細を確認
gcloud ai reasoning-engines describe RESOURCE_ID \
  --project=$PROJECT_ID \
  --region=us-central1
```

---

## デプロイ後のテスト

### test_agent.py を使用

デプロイしたエージェントをPythonでテストできます：

```bash
python test_agent.py
```

実行すると対話形式でエージェントをテストできます：

```
🧪 Agent Engine テスト
==================================================
📦 エージェント: bq_remote_agent
🆔 Resource ID: 6189323576076664832

👤 User ID: test-user-97a903d1
📝 セッションを作成中...
✅ セッションID: 4324746194048778240

💬 対話を開始します（終了: quit または exit）
--------------------------------------------------

🧑 You: BQにどんなデータがありますか？

🤖 Agent: 
BigQueryにどんなデータがあるか知るために、まずはデータセットの一覧を取得します...
```

### test_agent.py のカスタマイズ

別のエージェントをテストする場合は、ファイル内の設定を変更：

```python
# 設定
PROJECT_ID = "your-project-id"
LOCATION = "us-central1"
RESOURCE_ID = "your-resource-id"  # デプロイ時に取得したID
```

### cURL でテスト（API直接呼び出し）

REST API を直接呼び出してテストすることもできます：

```bash
# アクセストークン取得
ACCESS_TOKEN=$(gcloud auth print-access-token)

# セッション作成
curl -X POST "https://us-central1-aiplatform.googleapis.com/v1/projects/YOUR_PROJECT/locations/us-central1/reasoningEngines/RESOURCE_ID:streamQuery" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "class_method": "create_session",
    "input": {"user_id": "test-user-001"}
  }'
```

### Cloud Logs でデバッグ

エラーが発生した場合は Cloud Logs を確認：

```bash
gcloud logging read "resource.type=aiplatform.googleapis.com/ReasoningEngine" \
  --project=$PROJECT_ID \
  --limit=50 \
  --format="table(timestamp,severity,textPayload)"
```

---

## エージェントの更新

コードを変更した場合、再デプロイが必要です：

```bash
# 変更を加えた後
./deploy.sh
```

> **注意**: 再デプロイすると新しい Resource ID が発行されます。

### エージェントの削除

不要になったエージェントを削除：

```bash
gcloud ai reasoning-engines delete RESOURCE_ID \
  --project=$PROJECT_ID \
  --region=us-central1
```

---

## Gemini Enterpriseでの設定

Gemini Enterprise でエージェントを使用する場合、ユーザーの代わりに BigQuery にアクセスするための OAuth 設定が必要です。

### 1. OAuth 2.0 クライアントID作成

1. [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials
2. **Create Credentials** → **OAuth client ID**
3. Application type: **Web application**
4. Name: `BQ Agent OAuth`
5. Authorized redirect URIs に以下を追加:
   - `https://vertexaisearch.cloud.google.com/oauth-redirect`
6. **Create** をクリック
7. **Client ID** と **Client Secret** を控える

### 2. OAuth 同意画面の設定

1. APIs & Services → OAuth consent screen
2. User Type: **Internal**（組織内のみ）または **External**
3. App name: `BQ Agent`
4. Scopes に追加:
   - `https://www.googleapis.com/auth/bigquery`
5. Save

### 3. Gemini Enterprise でエージェント登録

1. [Google Cloud Console](https://console.cloud.google.com) → Gemini Enterprise
2. アプリを選択（または新規作成）
3. **Agents** → **Add Agent**
4. 以下を設定:
   - **Agent type**: ADK Agent
   - **Resource ID**: デプロイ時に取得した Resource ID
   - **Authorization**:
     - Client ID: 作成した OAuth Client ID
     - Client Secret: OAuth Client Secret
     - Auth URI: `https://accounts.google.com/o/oauth2/v2/auth?client_id=CLIENT_ID&redirect_uri=https://vertexaisearch.cloud.google.com/static/oauth/oauth.html&scope=https://www.googleapis.com/auth/bigquery&include_granted_scopes=true&response_type=code&access_type=offline&prompt=consent`
     - Token URI: `https://oauth2.googleapis.com/token`

---

## トラブルシューティング

### エラー: `gcloud beta services mcp` コマンドが見つからない

gcloud CLI のバージョンが古い、または beta コンポーネントがインストールされていません。

```bash
# gcloud を最新版にアップデート
gcloud components update

# beta コンポーネントをインストール
gcloud components install beta

# インストール確認
gcloud components list | grep beta

# 再度実行
gcloud beta services mcp enable bigquery.googleapis.com --project=$PROJECT_ID
```

それでもエラーが出る場合は、gcloud CLI を再インストールしてください。

### エラー: `Invalid choice: 'enable'` for mcp command

gcloud CLI のバージョンが MCP コマンドに対応していません。

```bash
# バージョン確認
gcloud version

# 最新版にアップデート
gcloud components update --quiet

# それでもダメな場合は gcloud CLI を再インストール
# macOS (Homebrew)
brew reinstall google-cloud-sdk

# 再度認証
gcloud auth login
gcloud auth application-default login
```

### エラー: 403 Forbidden - MCP Tool User role required

MCP Tool User ロールが付与されていません。

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$USER_EMAIL" \
  --role="roles/mcp.toolUser"
```

### エラー: BigQuery permission denied

BigQuery の権限が不足しています。

```bash
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$USER_EMAIL" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:$USER_EMAIL" \
  --role="roles/bigquery.jobUser"
```

### エラー: OAuth token refresh failed

ADC が正しく設定されていません。

```bash
# ADC を再設定
gcloud auth application-default login
```

### Agent Engine デプロイ後にエージェントが動かない

サービスアカウントの権限を確認してください。

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

# 権限を確認
gcloud projects get-iam-policy $PROJECT_ID \
  --filter="bindings.members:service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
  --format="table(bindings.role)"
```

### MCP Server が有効化できない

プロジェクトで必要なAPIが有効化されているか確認：

```bash
# 有効なAPIを確認
gcloud services list --enabled --project=$PROJECT_ID | grep -E "(bigquery|apihub|apiregistry)"

# 必要なAPIを有効化
gcloud services enable bigquery.googleapis.com --project=$PROJECT_ID
gcloud services enable apihub.googleapis.com --project=$PROJECT_ID
gcloud services enable cloudapiregistry.googleapis.com --project=$PROJECT_ID
```

---

## 参考リンク

- [ADK Documentation](https://google.github.io/adk-docs/)
- [BigQuery Remote MCP Server](https://cloud.google.com/bigquery/docs/use-bigquery-mcp)
- [Agent Engine](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/overview)
- [Gemini Enterprise](https://cloud.google.com/gemini/enterprise/docs/)
- [MCP (Model Context Protocol)](https://modelcontextprotocol.io/)
- [gcloud CLI インストール](https://cloud.google.com/sdk/docs/install?hl=ja)

---

## アーキテクチャ図

```
┌─────────────────────────────────────────────────────────────────┐
│                        Local Development                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐     ┌──────────────┐     ┌───────────────────┐   │
│  │ adk web  │────▶│ ADK Agent    │────▶│ BigQuery Remote   │   │
│  │ (UI)     │     │ (agent.py)   │     │ MCP Server        │   │
│  └──────────┘     └──────────────┘     └───────────────────┘   │
│                          │                      │               │
│                          │    ADC (OAuth)       │               │
│                          └──────────────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        Production (GCP)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────────┐  │
│  │ Gemini       │────▶│ Vertex AI    │────▶│ BigQuery       │  │
│  │ Enterprise   │     │ Agent Engine │     │ Remote MCP     │  │
│  │ (User)       │     │              │     │ Server         │  │
│  └──────────────┘     └──────────────┘     └────────────────┘  │
│         │                    │                     │            │
│         │                    │   Service Account   │            │
│         │    OAuth 2.0      └─────────────────────┘            │
│         └──────────────────────────────────────────             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 更新履歴

- 2026-01-04: デプロイ詳細手順、テストスクリプト、クイックスタート、プロジェクト構成を追加
- 2026-01-04: MCP有効化手順、gcloud CLIアップデート手順を追加
- 2026-01-03: 初版作成
