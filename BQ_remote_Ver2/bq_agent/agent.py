"""
BigQuery Remote MCP Server Agent for Agent Engine + Gemini Enterprise

デプロイ方法:
1. adk deploy agent_engine --project=agent-vi-473112 --region=us-central1
2. Gemini EnterpriseでOAuth設定してエージェント登録

Excel出力機能:
- execute_sqlの結果をExcelファイルとして保存可能
- ArtifactServiceを通じてファイルを管理
"""
import os
import json
from typing import Any
import google.auth
from google.auth.transport import requests as google_requests
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

# Excel出力用ツールをインポート
from .excel_tool import export_to_excel, list_saved_files

# BigQuery Remote MCP Server URL
BIGQUERY_MCP_URL = "https://bigquery.googleapis.com/mcp"

# プロジェクトID
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "agent-vi-473112")


def _get_auth_headers():
    """認証ヘッダーを取得"""
    credentials, project = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/bigquery",
            "https://www.googleapis.com/auth/cloud-platform"
        ]
    )
    
    auth_request = google_requests.Request()
    credentials.refresh(auth_request)
    
    return {
        "Authorization": f"Bearer {credentials.token}",
        "x-goog-user-project": project or PROJECT_ID
    }


# MCPToolset をグローバルで1回だけ初期化
_bigquery_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=BIGQUERY_MCP_URL,
        headers=_get_auth_headers()
    )
)


# Excel出力ツール定義
async def save_query_result_to_excel(
    query_result: str,
    filename: str,
    sheet_name: str = "QueryResult",
    tool_context: Any = None
) -> dict[str, Any]:
    """
    SQLクエリの結果をExcelファイルとして保存する
    
    Args:
        query_result: execute_sqlの結果（JSON文字列またはリスト）
        filename: 保存するファイル名（例: "sales_report.xlsx"）
        sheet_name: シート名（デフォルト: "QueryResult"）
        tool_context: ADKのToolContext
    
    Returns:
        dict: 保存結果
    """
    # 文字列の場合はJSONとしてパース
    if isinstance(query_result, str):
        try:
            data = json.loads(query_result)
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "query_resultのJSON解析に失敗しました。"
            }
    else:
        data = query_result
    
    # データがリストでない場合の処理
    if not isinstance(data, list):
        if isinstance(data, dict) and "rows" in data:
            data = data["rows"]
        elif isinstance(data, dict) and "result" in data:
            data = data["result"]
    
    return await export_to_excel(
        data=data,
        filename=filename,
        sheet_name=sheet_name,
        tool_context=tool_context
    )


# FunctionToolとして登録
excel_export_tool = FunctionTool(func=save_query_result_to_excel)
list_files_tool = FunctionTool(func=list_saved_files)


# エージェント定義
root_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="bq_remote_agent",
    description="BigQuery データ分析エージェント（Excel出力機能付き）",
    instruction=f"""あなたはBigQueryのデータ分析エキスパートです。

プロジェクトID: {PROJECT_ID}

## 利用可能なツール

### BigQuery操作
- list_dataset_ids: データセット一覧を取得
- list_table_ids: テーブル一覧を取得  
- get_table_info: テーブルのスキーマ情報を取得
- execute_sql: 任意のSQLクエリを実行

### ファイル出力
- save_query_result_to_excel: SQLクエリの結果をExcelファイルとして保存
  - query_result: execute_sqlの結果をそのまま渡す
  - filename: ファイル名（例: "sales_report.xlsx"）
  - sheet_name: シート名（オプション）
- list_saved_files: 保存済みファイル一覧を表示

## 重要なルール
1. ユーザーの質問に答えるために必要なツールは、説明なしに即座に実行してください
2. 「〜を取得します」「〜を実行します」と言う前に、まずツールを呼び出してください
3. ツールの結果を待ってから、結果をユーザーに説明してください
4. 1回のレスポンスで複数のツールを連続して呼び出すことができます

## Excel出力のワークフロー
1. execute_sql でデータを取得
2. 取得した結果を save_query_result_to_excel に渡して保存
3. 保存完了を報告

日本語で分かりやすく回答してください。
""",
    tools=[_bigquery_toolset, excel_export_tool, list_files_tool]
)
