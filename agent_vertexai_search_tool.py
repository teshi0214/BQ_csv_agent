"""
Vertex AI Search データストアを参照するADKエージェント
VertexAiSearchTool版（Enterprise Edition / Search App必要）

必要条件:
- Gemini Enterpriseライセンス
- Search App（Engine）の作成とデータストアの接続
- Discovery Engine User IAMロール
"""

from google.adk.agents import LlmAgent
from google.adk.tools import VertexAiSearchTool

# プロジェクト設定
PROJECT_ID = "agent-vi-473112"
DATASTORE_ID = "adk-test_1769691409159"
DATASTORE_REGION = "global"

# データストアのパス
DATASTORE_PATH = f"projects/{PROJECT_ID}/locations/{DATASTORE_REGION}/collections/default_collection/dataStores/{DATASTORE_ID}"

# Vertex AI Search ツール
vertex_search_tool = VertexAiSearchTool(data_store_id=DATASTORE_PATH)

# エージェント定義
root_agent = LlmAgent(
    name="vertex_search_agent",
    model="gemini-2.0-flash",  # Geminiモデル必須
    tools=[vertex_search_tool],
    instruction="""あなたはVertex AI Searchを使用してドキュメントを検索し、質問に回答するアシスタントです。

ユーザーからの質問に対して、データストア内のドキュメントを検索して回答してください。
検索結果に基づいて、正確で分かりやすい回答を日本語で提供してください。

情報が見つからない場合は、その旨を伝えてください。
""",
    description="Vertex AI Searchデータストアを検索して質問に回答するエージェント",
)




2026-01-30 10:57:18,686 - INFO - envs.py:47 - Loaded .env file for vertex_search at /mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.env
2026-01-30 10:57:18,691 - INFO - envs.py:47 - Loaded .env file for vertex_search at /mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.env
2026-01-30 10:57:18,729 - INFO - agent_loader.py:129 - Found root_agent in vertex_search.agent
2026-01-30 10:57:19,257 - INFO - google_llm.py:181 - Sending out request, model: gemini-2.0-flash, backend: GoogleLLMVariant.VERTEX_AI, stream: False
2026-01-30 10:57:19,257 - INFO - models.py:7012 - AFC is enabled with max remote calls: 10.
2026-01-30 10:57:33,487 - INFO - _client.py:1740 - HTTP Request: POST https://us-central1-aiplatform.googleapis.com/v1beta1/projects/sts-da-agentspace-dev/locations/us-central1/publishers/google/models/gemini-2.0-flash:generateContent "HTTP/1.1 200 OK"
2026-01-30 10:57:33,489 - INFO - google_llm.py:246 - Response received from the model.
