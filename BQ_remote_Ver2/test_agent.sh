#!/bin/bash
#
# test_agent.sh - デプロイしたエージェントをテスト
#

PROJECT_ID="agent-vi-473112"
REGION="us-central1"
RESOURCE_ID="6189323576076664832"

# アクセストークン取得
ACCESS_TOKEN=$(gcloud auth print-access-token)

# エンドポイント
ENDPOINT="https://${REGION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${REGION}/reasoningEngines/${RESOURCE_ID}:query"

echo "🧪 Agent Engine テスト"
echo "====================="
echo "Resource ID: $RESOURCE_ID"
echo "Endpoint: $ENDPOINT"
echo ""

# テストクエリ
read -p "質問を入力 (デフォルト: BQにどんなデータがありますか？): " QUERY
QUERY=${QUERY:-"BQにどんなデータがありますか？"}

echo ""
echo "📤 送信中..."
echo ""

curl -s -X POST "$ENDPOINT" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"input\": {
      \"messages\": [
        {
          \"role\": \"user\",
          \"parts\": [{\"text\": \"$QUERY\"}]
        }
      ]
    }
  }" | python3 -m json.tool 2>/dev/null || cat

echo ""
