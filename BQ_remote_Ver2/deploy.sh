#!/bin/bash
#
# deploy.sh - Agent Engine へのデプロイスクリプト
#
# 使用方法:
#   chmod +x deploy.sh
#   ./deploy.sh
#   ./deploy.sh --display-name "My BQ Agent"
#

set -e

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

# スクリプトのディレクトリに移動
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "BigQuery MCP Agent - デプロイ"
echo "========================================"

# ===========================================
# 1. 前提条件チェック
# ===========================================
echo ""
info "前提条件をチェック中..."

# 仮想環境チェック
if [ ! -d ".venv" ]; then
    error "仮想環境が見つかりません。先に ./setup.sh を実行してください"
fi

# agent.py チェック
if [ ! -f "bq_agent/agent.py" ]; then
    error "bq_agent/agent.py が見つかりません"
fi

# .env チェック
if [ ! -f ".env" ]; then
    error ".env ファイルが見つかりません。先に ./setup.sh を実行してください"
fi

# ===========================================
# 2. 環境変数読み込み
# ===========================================
info "環境変数を読み込み中..."
set -a
source .env
set +a

if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    error "GOOGLE_CLOUD_PROJECT が設定されていません"
fi

info "プロジェクト: $GOOGLE_CLOUD_PROJECT"
info "リージョン: ${GOOGLE_CLOUD_LOCATION:-us-central1}"

# ===========================================
# 3. 仮想環境を有効化
# ===========================================
info "仮想環境を有効化中..."
source .venv/bin/activate

# adk コマンド確認
if ! command -v adk &> /dev/null; then
    error "adk コマンドが見つかりません。pip install google-adk を実行してください"
fi

info "ADK version: $(adk --version 2>/dev/null || echo 'unknown')"

# ===========================================
# 4. デプロイ実行
# ===========================================
echo ""
info "Agent Engine にデプロイ中..."
echo ""

# deploy.py を実行（引数をそのまま渡す）
python deploy.py \
    --project "$GOOGLE_CLOUD_PROJECT" \
    --region "${GOOGLE_CLOUD_LOCATION:-us-central1}" \
    "$@"

# ===========================================
# 5. デプロイ確認
# ===========================================
echo ""
info "デプロイされたエージェントを確認中..."
echo ""

gcloud ai reasoning-engines list \
    --project="$GOOGLE_CLOUD_PROJECT" \
    --region="${GOOGLE_CLOUD_LOCATION:-us-central1}" \
    --format="table(name.basename(), displayName, createTime)" \
    2>/dev/null || warn "エージェント一覧の取得に失敗しました"

echo ""
echo "========================================"
echo -e "${GREEN}デプロイスクリプト完了${NC}"
echo "========================================"
