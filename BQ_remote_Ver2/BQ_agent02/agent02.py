from google.adk.agents import Agent
from google.adk.tools import ApiRegistry, FunctionTool
from .excel_tool import export_to_excel, list_saved_files

# プロジェクトID
PROJECT_ID = "agent-vi-473112"

# MCP サーバー (Google Cloud API Registry)
MCP_SERVER_NAME = f"projects/{PROJECT_ID}/locations/global/mcpServers/google-bigquery.googleapis.com-mcp"

# ヘッダー設定 (BigQuery用にプロジェクトヘッダーが必要)
header_provider = lambda context: {
    "x-goog-user-project": PROJECT_ID,
}

# ApiRegistry初期化
bq_api_registry = ApiRegistry(PROJECT_ID, header_provider=header_provider)

# BigQuery MCP serverのtoolsetを取得
registry_tools = bq_api_registry.get_toolset(
    mcp_server_name=MCP_SERVER_NAME
)

# Excel出力ツール
excel_export_tool = FunctionTool(func=export_to_excel)
list_files_tool = FunctionTool(func=list_saved_files)

# エージェント定義
root_agent = Agent(
    name="bigquery_mcp_agent",
    model="gemini-2.5-flash",
    tools=[registry_tools, excel_export_tool, list_files_tool],
    instruction=f"""あなたはBigQueryの専門家です。
プロジェクトID '{PROJECT_ID}' をデフォルトとして使用し、
積極的にBigQueryのツールを使って回答してください。

## 利用可能なツール

### BigQuery操作
- list_dataset_ids: データセットを一覧表示
- list_table_ids: テーブルを一覧表示
- get_dataset_info: データセットのメタデータを取得
- get_table_info: テーブルのメタデータを取得
- execute_sql: SQLステートメントを実行
- search_catalog: 自然言語を使用してテーブルを検索

### Excel出力
- export_to_excel: クエリ結果をExcelファイルとして保存
  - data: execute_sqlの結果データ
  - filename: ファイル名（例: "report.xlsx"）
  - sheet_name: シート名（オプション、デフォルト: "Sheet1"）
- list_saved_files: 保存済みファイル一覧を表示

## 重要なルール
1. ユーザーの質問に答えるために必要なツールは、説明なしに即座に実行してください
2. 「〜を取得します」「〜を実行します」と言う前に、まずツールを呼び出してください
3. ツールの結果を待ってから、結果をユーザーに説明してください

## Excel出力のワークフロー
1. execute_sql でデータを取得
2. 取得した結果を export_to_excel に渡して保存
3. 保存完了を報告

日本語で分かりやすく回答してください。
""",
)
