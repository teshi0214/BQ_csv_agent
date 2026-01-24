"""
Excel出力ツール (Artifacts機能使用)
"""
import json
from io import BytesIO
from typing import Any
import google.genai.types as types
from google.adk.tools import ToolContext


async def export_to_excel(
    tool_context: ToolContext,
    data: list[dict[str, Any]] | str,
    filename: str,
    sheet_name: str = "Sheet1",
) -> dict[str, Any]:
    """
    データをExcelファイルとしてArtifactに保存する
    
    Args:
        tool_context: ADKのToolContext（自動注入）
        data: 保存するデータ（辞書のリスト or JSON文字列）
        filename: ファイル名（例: "report.xlsx"）
        sheet_name: シート名
    
    Returns:
        dict: 保存結果
    """
    try:
        from openpyxl import Workbook
    except ImportError:
        return {
            "success": False,
            "error": "openpyxlがインストールされていません。pip install openpyxl を実行してください。"
        }
    
    # JSON文字列の場合はパース
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return {
                "success": False,
                "error": "JSONの解析に失敗しました。"
            }
    
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
        return {
            "success": False,
            "error": "保存するデータがありません。"
        }
    
    # Excelワークブック作成
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    
    # ヘッダー行を書き込み
    if isinstance(data[0], dict):
        headers = list(data[0].keys())
        ws.append(headers)
        
        # データ行を書き込み
        for row in data:
            ws.append([row.get(h, "") for h in headers])
    else:
        # リストのリストの場合
        for row in data:
            if isinstance(row, list):
                ws.append(row)
            else:
                ws.append([row])
    
    # BytesIOに保存
    excel_buffer = BytesIO()
    wb.save(excel_buffer)
    excel_bytes = excel_buffer.getvalue()
    
    # ファイル名に.xlsxがなければ追加
    if not filename.endswith(".xlsx"):
        filename = f"{filename}.xlsx"
    
    # Artifactとして保存
    try:
        artifact = types.Part.from_bytes(
            data=excel_bytes,
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        version = await tool_context.save_artifact(filename=filename, artifact=artifact)
        
        return {
            "success": True,
            "filename": filename,
            "version": version,
            "rows": len(data),
            "message": f"Excelファイル '{filename}' を保存しました（バージョン: {version}、{len(data)}行）"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Artifactの保存に失敗しました: {str(e)}"
        }


async def list_saved_files(tool_context: ToolContext) -> dict[str, Any]:
    """
    保存済みのArtifact一覧を取得する
    
    Args:
        tool_context: ADKのToolContext（自動注入）
    
    Returns:
        dict: ファイル一覧
    """
    try:
        files = await tool_context.list_artifacts()
        return {
            "success": True,
            "files": files if files else [],
            "count": len(files) if files else 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"ファイル一覧の取得に失敗しました: {str(e)}"
        }
