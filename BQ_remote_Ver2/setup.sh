#!/bin/bash
#
# setup.sh - 環境セットアップスクリプト
#
# 使用方法:
#   chmod +x setup.sh
#   ./setup.sh
#

set -e  # エラー時に停止

echo "========================================"
echo "BigQuery MCP Agent - 環境セットアップ"
echo "========================================"

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ヘルパー関数
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# ===========================================
# 1. 前提条件チェック
# ===========================================
echo ""
info "前提条件をチェック中..."

# Python チェック
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    info "Python: $PYTHON_VERSION"
else
    error "Python3 がインストールされていません"
fi

# gcloud チェック
if command -v gcloud &> /dev/null; then
    GCLOUD_VERSION=$(gcloud version 2>&1 | head -1)
    info "gcloud: $GCLOUD_VERSION"
else
    error "gcloud CLI がインストールされていません。https://cloud.google.com/sdk/docs/install からインストールしてください"
fi

# uv チェック（オプション）
if command -v uv &> /dev/null; then
    UV_VERSION=$(uv --version 2>&1)
    info "uv: $UV_VERSION"
    USE_UV=true
else
    warn "uv がインストールされていません。pip を使用します"
    USE_UV=false
fi

# ===========================================
# 2. gcloud CLI アップデート
# ===========================================
echo ""
info "gcloud CLI をアップデート中..."

gcloud components update --quiet || warn "gcloud components update に失敗しました（権限の問題かもしれません）"

# beta コンポーネントのインストール
info "beta コンポーネントをインストール中..."
gcloud components install beta --quiet 2>/dev/null || warn "beta コンポーネントは既にインストールされているか、インストールに失敗しました"

# ===========================================
# 3. プロジェクトID設定
# ===========================================
echo ""

# .env ファイルからプロジェクトIDを読み込む
if [ -f .env ]; then
    source .env 2>/dev/null || true
fi

# 環境変数またはユーザー入力からプロジェクトIDを取得
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    read -p "Google Cloud プロジェクトIDを入力してください: " PROJECT_ID
else
    PROJECT_ID=$GOOGLE_CLOUD_PROJECT
    info "プロジェクトID: $PROJECT_ID (.envから読み込み)"
    read -p "このプロジェクトIDを使用しますか？ [Y/n]: " confirm
    if [[ $confirm =~ ^[Nn]$ ]]; then
        read -p "新しいプロジェクトIDを入力してください: " PROJECT_ID
    fi
fi

# プロジェクトIDのバリデーション
if [ -z "$PROJECT_ID" ]; then
    error "プロジェクトIDが指定されていません"
fi

export PROJECT_ID

# gcloud プロジェクト設定
info "gcloud プロジェクトを設定中..."
gcloud config set project $PROJECT_ID

# ===========================================
# 4. 認証
# ===========================================
echo ""
info "認証状態を確認中..."

# 認証チェック
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 &> /dev/null; then
    warn "認証されていません。ログインを開始します..."
    gcloud auth login
fi

ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)
info "アクティブアカウント: $ACTIVE_ACCOUNT"

# ADC設定確認
if [ ! -f "$HOME/.config/gcloud/application_default_credentials.json" ]; then
    warn "Application Default Credentials が設定されていません"
    read -p "ADC を設定しますか？ [Y/n]: " setup_adc
    if [[ ! $setup_adc =~ ^[Nn]$ ]]; then
        gcloud auth application-default login
    fi
else
    info "Application Default Credentials: 設定済み"
fi

# ===========================================
# 5. API有効化
# ===========================================
echo ""
info "必要なAPIを有効化中..."

APIS=(
    "bigquery.googleapis.com"
    "aiplatform.googleapis.com"
    "cloudresourcemanager.googleapis.com"
    "apihub.googleapis.com"
)

for api in "${APIS[@]}"; do
    info "  有効化中: $api"
    gcloud services enable $api --project=$PROJECT_ID --quiet || warn "  $api の有効化に失敗しました"
done

# ===========================================
# 6. MCP Server 有効化
# ===========================================
echo ""
info "BigQuery MCP Server を有効化中..."

if gcloud beta services mcp enable bigquery.googleapis.com --project=$PROJECT_ID 2>/dev/null; then
    info "BigQuery MCP Server: 有効化成功"
else
    warn "BigQuery MCP Server の有効化に失敗しました"
    warn "gcloud CLI のバージョンが古い可能性があります"
    warn "手動で実行してください: gcloud beta services mcp enable bigquery.googleapis.com --project=$PROJECT_ID"
fi

# ===========================================
# 7. IAM権限設定
# ===========================================
echo ""
info "IAM権限を設定中..."

# MCP Tool User ロール
info "  MCP Tool User ロールを付与中..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="user:$ACTIVE_ACCOUNT" \
    --role="roles/mcp.toolUser" \
    --quiet 2>/dev/null || warn "  MCP Tool User ロールの付与に失敗しました"

# BigQuery 権限
info "  BigQuery 権限を付与中..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="user:$ACTIVE_ACCOUNT" \
    --role="roles/bigquery.dataViewer" \
    --quiet 2>/dev/null || true

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="user:$ACTIVE_ACCOUNT" \
    --role="roles/bigquery.jobUser" \
    --quiet 2>/dev/null || true

# ===========================================
# 8. Python環境セットアップ
# ===========================================
echo ""
info "Python仮想環境をセットアップ中..."

if [ ! -d ".venv" ]; then
    if [ "$USE_UV" = true ]; then
        uv venv --python 3.11
    else
        python3 -m venv .venv
    fi
    info "仮想環境を作成しました"
else
    info "仮想環境は既に存在します"
fi

# 仮想環境を有効化
source .venv/bin/activate

# パッケージインストール
info "パッケージをインストール中..."
if [ "$USE_UV" = true ]; then
    uv pip install -r requirements.txt
else
    pip install -r requirements.txt
fi

# ===========================================
# 9. .env ファイル更新
# ===========================================
echo ""
info ".env ファイルを更新中..."

cat << EOF > .env
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=1
EOF

info ".env ファイルを更新しました"

# ===========================================
# 完了
# ===========================================
echo ""
echo "========================================"
echo -e "${GREEN}セットアップ完了！${NC}"
echo "========================================"
echo ""
echo "次のステップ:"
echo "  1. ローカルテスト:  source .venv/bin/activate && adk web"
echo "  2. デプロイ:        ./deploy.sh"
echo ""
