#!/usr/bin/env python3
"""
test_agent.py - デプロイしたエージェントをテスト
"""

import uuid
import vertexai
from vertexai import agent_engines

# 設定
PROJECT_ID = "agent-vi-473112"
LOCATION = "us-central1"
RESOURCE_ID = "6189323576076664832"

def extract_text(event):
    """イベントからテキストを抽出"""
    texts = []
    
    if isinstance(event, dict):
        content = event.get('content', {})
        parts = content.get('parts', [])
        for part in parts:
            if isinstance(part, dict) and 'text' in part:
                texts.append(part['text'])
    
    return ''.join(texts)


def main():
    print("🧪 Agent Engine テスト")
    print("=" * 50)
    
    # Vertex AI 初期化
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    # Agent Engine を取得
    agent = agent_engines.get(f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{RESOURCE_ID}")
    
    print(f"📦 エージェント: {agent.display_name or 'bq_remote_agent'}")
    print(f"🆔 Resource ID: {RESOURCE_ID}")
    print()
    
    # ユーザーID生成
    user_id = f"test-user-{uuid.uuid4().hex[:8]}"
    print(f"👤 User ID: {user_id}")
    
    # セッション作成
    print("📝 セッションを作成中...")
    session = agent.create_session(user_id=user_id)
    session_id = session["id"]
    print(f"✅ セッションID: {session_id}")
    print()
    
    # 対話ループ
    print("💬 対話を開始します（終了: quit または exit）")
    print("-" * 50)
    
    while True:
        try:
            query = input("\n🧑 You: ").strip()
            if not query:
                continue
            if query.lower() in ["quit", "exit", "q"]:
                break
            
            print("\n🤖 Agent: ", flush=True)
            
            # ストリーミングでレスポンス取得
            full_response = []
            for event in agent.stream_query(
                user_id=user_id,
                session_id=session_id,
                message=query
            ):
                text = extract_text(event)
                if text:
                    full_response.append(text)
                    print(text, end="", flush=True)
            
            if not full_response:
                print("(処理中...)")
            
            print()  # 改行
            
        except KeyboardInterrupt:
            print("\n\n中断されました")
            break
        except Exception as e:
            print(f"\n❌ エラー: {e}")
            import traceback
            traceback.print_exc()
    
    # セッション削除
    print("\n🗑️ セッションを削除中...")
    agent.delete_session(user_id=user_id, session_id=session_id)
    print("✅ セッション削除完了")
    print("\n👋 終了")


if __name__ == "__main__":
    main()
