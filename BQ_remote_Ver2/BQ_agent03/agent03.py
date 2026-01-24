from google.adk.agents import Agent
from google.adk.tools import ApiRegistry, FunctionTool, ToolContext
from io import StringIO
from typing import Any
import google.genai.types as types

# プロジェクトID
PROJECT_ID = "agent-vi-473112"

# MCP サーバー
MCP_SERVER_NAME = f"projects/{PROJECT_ID}/locations/global/mcpServers/google-bigquery.googleapis.com-mcp"

# ヘッダー設定
header_provider = lambda context: {
    "x-goog-user-project": PROJECT_ID,
}

# ApiRegistry初期化
bq_api_registry = ApiRegistry(PROJECT_ID, header_provider=header_provider)

# BigQuery MCP serverのtoolsetを取得
registry_tools = bq_api_registry.get_toolset(
    mcp_server_name=MCP_SERVER_NAME
)


# CSV出力ツール
async def export_to_csv(
    tool_context: ToolContext,
    data: list[dict[str, Any]] | str,
    filename: str,
) -> dict[str, Any]:
    """データをCSVファイルとしてArtifactに保存する"""
    import json
    
    # JSON文字列の場合はパース
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return {"success": False, "error": "JSONの解析に失敗しました。"}
    
    # データがリストでない場合の処理
    if not isinstance(data, list):
        if isinstance(data, dict):
            if "rows" in data:
                data = data["rows"]
            elif "result" in data:
                data = data["result"]
            else:
                data = [data]
    
    if not data:
        return {"success": False, "error": "保存するデータがありません。"}
    
    # CSV作成
    if isinstance(data[0], dict):
        headers = list(data[0].keys())
        lines = [",".join(headers)]
        for row in data:
            lines.append(",".join(str(row.get(h, "")) for h in headers))
        csv_content = "\n".join(lines)
    else:
        return {"success": False, "error": "データ形式がサポートされていません。"}
    
    # ファイル名に.csvがなければ追加
    if not filename.endswith(".csv"):
        filename = f"{filename}.csv"
    
    # Artifactとして保存
    try:
        artifact = types.Part.from_bytes(
            data=csv_content.encode("utf-8"),
            mime_type="text/csv"
        )
        version = await tool_context.save_artifact(filename=filename, artifact=artifact)
        
        return {
            "success": True,
            "filename": filename,
            "version": version,
            "rows": len(data),
            "message": f"CSVファイル '{filename}' を保存しました"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


csv_export_tool = FunctionTool(func=export_to_csv)


# エージェント定義
root_agent = Agent(
    name="bigquery_mcp_agent",
    model="gemini-2.5-flash",
    tools=[registry_tools, csv_export_tool],
    instruction=f"""あなたはBigQueryの専門家です。
プロジェクトID '{PROJECT_ID}' をデフォルトとして使用してください。

CSVに出力してと依頼されたら、export_to_csv ツールを使ってください。
""",
)