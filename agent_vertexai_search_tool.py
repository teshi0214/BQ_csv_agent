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
