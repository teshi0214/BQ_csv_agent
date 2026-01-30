"""
Vertex AI Search データストアを参照するADKエージェント
VertexAiSearchTool版（Enterprise Edition / Search App必要）
デバッグ版

必要条件:
- Gemini Enterpriseライセンス
- Search App（Engine）の作成とデータストアの接続
- Discovery Engine User IAMロール
"""

import logging
from google.adk.agents import LlmAgent
from google.adk.tools import VertexAiSearchTool

# デバッグログ有効化
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# プロジェクト設定
PROJECT_ID = "sts-da-agentspace-dev"
DATASTORE_ID = "adk-test_1769691409159"  # 実際のデータストアIDに変更
DATASTORE_REGION = "global"

# データストアのパス
DATASTORE_PATH = f"projects/{PROJECT_ID}/locations/{DATASTORE_REGION}/collections/default_collection/dataStores/{DATASTORE_ID}"

logger.info(f"=== VertexAiSearchTool Configuration ===")
logger.info(f"Project ID: {PROJECT_ID}")
logger.info(f"Datastore ID: {DATASTORE_ID}")
logger.info(f"Datastore Path: {DATASTORE_PATH}")

# Vertex AI Search ツール
vertex_search_tool = VertexAiSearchTool(data_store_id=DATASTORE_PATH)

logger.info(f"VertexAiSearchTool created: {vertex_search_tool}")

# エージェント定義
root_agent = LlmAgent(
    name="vertex_search_agent",
    model="gemini-2.0-flash",  # Geminiモデル必須
    tools=[vertex_search_tool],
    instruction="""あなたはVertex AI Searchを使用してドキュメントを検索し、質問に回答するアシスタントです。

ユーザーからの質問に対して、必ずデータストア内のドキュメントを検索して回答してください。

検索を実行し、検索結果に基づいて回答を生成してください。
情報が見つからない場合は、「検索結果が見つかりませんでした」と回答してください。

日本語で回答してください。
""",
    description="Vertex AI Searchデータストアを検索して質問に回答するエージェント",
)

logger.info(f"Agent created with tools: {root_agent.tools}")
