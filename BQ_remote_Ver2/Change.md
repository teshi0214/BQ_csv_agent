# ADK Artifacts機能 - なぜ動かなかったのか？

## まず結論から

君のコードが動かなかった理由は、**ADKでファイルを保存する方法が根本的に違っていた**からです。

難しく考えなくて大丈夫。ポイントは1つだけ：

> **「ToolContext」を使ってファイルを保存する**

これだけ覚えればOK。

---

## 君のコードの何がダメだったか

### ❌ 問題1: インポートの書き方が古い

```python
# 君が書いたコード
from google.adk.agents.llm_agent import Agent
from google.adk.tools.api_registry import ApiRegistry
```

これ、ADKのバージョンが上がって書き方が変わったんだよね。

```python
# 正しい書き方（シンプルになった）
from google.adk.agents import Agent
from google.adk.tools import ApiRegistry
```

ネットで調べたコードは古いバージョンの可能性があるから注意！

---

### ❌ 問題2: `UnsafeLocalCodeExecutor`は使わない

```python
# 君が書いたコード
python_executor = UnsafeLocalCodeExecutor(artifact_service=artifact_service)
root_agent = Agent(..., code_executor=python_executor)
```

これ、何をしようとしてたかわかる？

`code_executor`っていうのは「エージェントにPythonコードを自由に書かせて実行させる」機能なんだよ。

でも今回やりたいのは「ファイルを保存する」だけでしょ？
それなら`code_executor`は必要ない。もっとシンプルな方法がある。

---

### ❌ 問題3: 存在しないものを使おうとした

```python
# 既存コード
root_agent.model_config["artifact_service"] = artifact_service
```

これ、エラーになるよ。`model_config`っていう設定項目は存在しない。

あと、instructionに書いてた `artifact_service.create_artifact()` も存在しないメソッド。

---

## じゃあどうすればいいの？

### 正しい方法: FunctionTool + ToolContext

ADKでファイルを保存するときは、こういう流れになる：

```
1. 自分で「ファイル保存用の関数」を作る
2. その関数の中で「ToolContext.save_artifact()」を呼ぶ
3. その関数をエージェントのツールとして登録する
```

図で書くとこう：

```
ユーザー: 「CSVで保存して」
    ↓
エージェント: 「export_to_csv ツールを呼ぼう」
    ↓
export_to_csv関数が実行される
    ↓
関数の中で tool_context.save_artifact() を呼ぶ
    ↓
ファイルが保存される！
```

---

## 実際のコード（これをコピペすればOK）

```python
from google.adk.agents import Agent
from google.adk.tools import ApiRegistry, FunctionTool, ToolContext
from typing import Any
import google.genai.types as types

# プロジェクトID（自分のに変えてね）
PROJECT_ID = "your-project-id"

# BigQuery MCP サーバーの設定
MCP_SERVER_NAME = f"projects/{PROJECT_ID}/locations/global/mcpServers/google-bigquery.googleapis.com-mcp"

header_provider = lambda context: {
    "x-goog-user-project": PROJECT_ID,
}

bq_api_registry = ApiRegistry(PROJECT_ID, header_provider=header_provider)
registry_tools = bq_api_registry.get_toolset(mcp_server_name=MCP_SERVER_NAME)


# ★ここが重要！ファイル保存用の関数を自分で作る
async def export_to_csv(
    tool_context: ToolContext,  # ← これが魔法の引数。ADKが自動で渡してくれる
    data: list[dict[str, Any]] | str,
    filename: str,
) -> dict[str, Any]:
    """データをCSVファイルとして保存する"""
    import json
    
    # 文字列で来たらJSONとしてパース
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            return {"success": False, "error": "JSONの解析に失敗"}
    
    # リストじゃなかったらリストにする
    if not isinstance(data, list):
        if isinstance(data, dict):
            data = data.get("rows") or data.get("result") or [data]
    
    if not data:
        return {"success": False, "error": "データがない"}
    
    # CSVを作る
    headers = list(data[0].keys())
    lines = [",".join(headers)]
    for row in data:
        lines.append(",".join(str(row.get(h, "")) for h in headers))
    csv_content = "\n".join(lines)
    
    # ファイル名の調整
    if not filename.endswith(".csv"):
        filename = f"{filename}.csv"
    
    # ★ここでファイルを保存！
    try:
        artifact = types.Part.from_bytes(
            data=csv_content.encode("utf-8"),
            mime_type="text/csv"
        )
        version = await tool_context.save_artifact(filename=filename, artifact=artifact)
        
        return {
            "success": True,
            "filename": filename,
            "message": f"保存したよ！"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# 関数をツールとして登録
csv_export_tool = FunctionTool(func=export_to_csv)


# エージェントを作る
root_agent = Agent(
    name="bigquery_agent",
    model="gemini-2.5-flash",
    tools=[registry_tools, csv_export_tool],  # ← ツールをリストで渡す
    instruction=f"""あなたはBigQueryの専門家です。
プロジェクトID '{PROJECT_ID}' を使ってください。
CSVに出力してと言われたら export_to_csv を使ってね。
""",
)
```

---

## InMemoryArtifactServiceについて

前に「検証では`InMemoryArtifactService`を使おう」って言ったよね。

**`InMemoryArtifactService`自体は正しい**よ！問題だったのは使い方。

```python
# これは正しい（ADK WEBでは自動で設定されるから書かなくてもOK）
artifact_service = InMemoryArtifactService()

# ❌ これが間違い - UnsafeLocalCodeExecutorに渡しても意味ない
python_executor = UnsafeLocalCodeExecutor(artifact_service=artifact_service)

# ❌ これも間違い - model_configは存在しない
root_agent.model_config["artifact_service"] = artifact_service
```

実は**ADK WEBを使う場合は、自分で`InMemoryArtifactService`を書く必要すらない**。
ADK WEBが自動でセットアップしてくれるから。

自分で書くのは`tool_context.save_artifact()`を呼ぶ関数だけでOK！

ちなみに本番環境では`GcsArtifactService`（Google Cloud Storage）を使うけど、
検証段階では`InMemoryArtifactService`で十分。ADK WEBがデフォルトで使ってるのもこれ。

---

## よくある質問

### Q: `tool_context`ってどこから来るの？

A: ADKが自動で渡してくれる！関数の引数に`tool_context: ToolContext`って書いておくだけでOK。LLMからは見えないから、ユーザーが指定する必要はない。

### Q: Excelも保存できる？

A: できる！`openpyxl`ライブラリを使えばいい。MIMEタイプを変えるだけ：

```python
# CSVの場合
mime_type="text/csv"

# Excelの場合
mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
```

### Q: 保存したファイルはどこで見れる？

A: ADK WEBの左側に「Artifacts」タブがある。ただし、**保存後にブラウザをリロード**しないと表示されないことがあるから注意！

### Q: `__init__.py`って何？

A: Pythonがそのフォルダを「モジュール」として認識するために必要なファイル。中身はこれだけでOK：

```python
from .agent import root_agent
```

`.agent`の部分は、自分のファイル名に合わせて変えてね。

---

## まとめ

1. **インポートはシンプルに**: `from google.adk.agents import Agent`
2. **UnsafeLocalCodeExecutorは使わない**: 今回の用途には不要
3. **ファイル保存はFunctionTool + ToolContext**: これが正しい方法
4. **`tool_context.save_artifact()`でファイルを保存**: ADKが自動で渡してくれる

