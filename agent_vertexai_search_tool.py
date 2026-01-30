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




404 NOT_FOUND。{'error': {'code': 404, 'message': 'データストア projects/89612432694/locations/global/collections/default_collection/dataStores/adk-test_1769691409159 が見つかりません。', 'status': 'NOT_FOUND'}}
INFO:     127.0.0.1:59212 - "POST /run_sse HTTP/1.1" 200 OK
2026-01-30 14:25:06,908 - INFO - envs.py:47 - Loaded .env file for vertex_search at /mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.env
2026-01-30 14:25:06,912 - INFO - envs.py:47 - Loaded .env file for vertex_search at /mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.env
2026-01-30 14:25:06,957 - INFO - agent.py:28 - === VertexAiSearchTool Configuration ===
2026-01-30 14:25:06,957 - INFO - agent.py:29 - Project ID: sts-da-agentspace-dev
2026-01-30 14:25:06,957 - INFO - agent.py:30 - Datastore ID: adk-test_1769691409159
2026-01-30 14:25:06,957 - INFO - agent.py:31 - Datastore Path: projects/sts-da-agentspace-dev/locations/global/collections/default_collection/dataStores/adk-test_1769691409159
2026-01-30 14:25:06,957 - INFO - agent.py:36 - VertexAiSearchTool created: <google.adk.tools.vertex_ai_search_tool.VertexAiSearchTool object at 0x718e39427590>
2026-01-30 14:25:06,957 - INFO - agent.py:55 - Agent created with tools: [<google.adk.tools.vertex_ai_search_tool.VertexAiSearchTool object at 0x718e39427590>]
2026-01-30 14:25:06,958 - INFO - agent_loader.py:129 - Found root_agent in vertex_search.agent
2026-01-30 14:25:07,520 - INFO - google_llm.py:181 - Sending out request, model: gemini-2.0-flash, backend: GoogleLLMVariant.VERTEX_AI, stream: False
2026-01-30 14:25:07,520 - INFO - models.py:7012 - AFC is enabled with max remote calls: 10.
2026-01-30 14:25:21,499 - INFO - _client.py:1740 - HTTP Request: POST https://us-central1-aiplatform.googleapis.com/v1beta1/projects/sts-da-agentspace-dev/locations/us-central1/publishers/google/models/gemini-2.0-flash:generateContent "HTTP/1.1 404 Not Found"
2026-01-30 14:25:21,684 - ERROR - adk_web_server.py:1509 - Error in event_generator: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'DataStore projects/89612432694/locations/global/collections/default_collection/dataStores/adk-test_1769691409159 not found.', 'status': 'NOT_FOUND'}}
Traceback (most recent call last):
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/adk/cli/adk_web_server.py", line 1499, in event_generator
    async for event in agen:
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/adk/runners.py", line 505, in run_async
    async for event in agen:
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/adk/runners.py", line 493, in _run_with_trace
    async for event in agen:
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/adk/runners.py", line 722, in _exec_with_plugin
    async for event in agen:
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/adk/runners.py", line 482, in execute
    async for event in agen:
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/adk/agents/base_agent.py", line 294, in run_async
    async for event in agen:
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/adk/agents/llm_agent.py", line 460, in _run_async_impl
    async for event in agen:
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/adk/flows/llm_flows/base_llm_flow.py", line 370, in run_async
    async for event in agen:
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/adk/flows/llm_flows/base_llm_flow.py", line 447, in _run_one_step_async
    async for llm_response in agen:
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/adk/flows/llm_flows/base_llm_flow.py", line 816, in _call_llm_async
    async for event in agen:
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/adk/flows/llm_flows/base_llm_flow.py", line 800, in _call_llm_with_tracing
    async for llm_response in agen:
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/adk/flows/llm_flows/base_llm_flow.py", line 1053, in _run_and_handle_error
    raise model_error
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/adk/flows/llm_flows/base_llm_flow.py", line 1039, in _run_and_handle_error
    async for response in agen:
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/adk/models/google_llm.py", line 262, in generate_content_async
    raise ce
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/adk/models/google_llm.py", line 241, in generate_content_async
    response = await self.api_client.aio.models.generate_content(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/genai/models.py", line 7018, in generate_content
    response = await self._generate_content(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/genai/models.py", line 5824, in _generate_content
    response = await self._api_client.async_request(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/genai/_api_client.py", line 1434, in async_request
    result = await self._async_request(
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/genai/_api_client.py", line 1367, in _async_request
    return await self._async_retry(  # type: ignore[no-any-return]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/tenacity/asyncio/__init__.py", line 111, in __call__
    do = await self.iter(retry_state=retry_state)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/tenacity/asyncio/__init__.py", line 153, in iter
    result = await action(retry_state)
             ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/tenacity/_utils.py", line 99, in inner
    return call(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/tenacity/__init__.py", line 420, in exc_check
    raise retry_exc.reraise()
          ^^^^^^^^^^^^^^^^^^^
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/tenacity/__init__.py", line 187, in reraise
    raise self.last_attempt.result()
          ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/s-teshigahara/.pyenv/versions/3.11.6/lib/python3.11/concurrent/futures/_base.py", line 449, in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
  File "/home/s-teshigahara/.pyenv/versions/3.11.6/lib/python3.11/concurrent/futures/_base.py", line 401, in __get_result
    raise self._exception
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/tenacity/asyncio/__init__.py", line 114, in __call__
    result = await fn(*args, **kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/genai/_api_client.py", line 1347, in _async_request_once
    await errors.APIError.raise_for_async_response(client_response)
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/genai/errors.py", line 203, in raise_for_async_response
    await cls.raise_error_async(status_code, response_json, response)
  File "/mnt/c/Users/s-teshigahara/OneDrive - 株式会社システムサポート/デスクトップ/BQ_remote/.venv/lib/python3.11/site-packages/google/genai/errors.py", line 225, in raise_error_async
    raise ClientError(status_code, response_json, response)
google.genai.errors.ClientError: 404 NOT_FOUND. {'error': {'code': 404, 'message': 'DataStore projects/89612432694/locations/global/collections/default_collection/dataStores/adk-test_1769691409159 not found.', 'status': 'NOT_FOUND'}}
INFO:     127.0.0.1:59212 - "GET /debug/trace/session/161937dc-a2aa-441e-bdcb-35cd7a918200 HTTP/1.1" 200 OK

